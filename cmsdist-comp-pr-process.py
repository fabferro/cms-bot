#!/usr/bin/env python
from sys import exit
from re import match
from github import Github
from os.path import expanduser
from optparse import OptionParser
from socket import setdefaulttimeout
from cmsdist_merge_permissions import USERS_TO_TRIGGER_HOOKS, getCommentCommand, hasRights
from process_pr import get_changed_files
setdefaulttimeout(120)

def process_pr(gh, repo, issue, dryRun):
  print "Issue state:", issue.state
  prId    = issue.number
  pr      = None
  branch  = None
  cmdType = None
  chg_files= []
  if issue.pull_request:
    pr   = repo.get_pull(prId)
    branch = pr.base.ref
    print "PR merged:", pr.merged
    if pr.merged: return True
    chg_files = process_pr(pr)
  USERS_TO_TRIGGER_HOOKS.add("cmsbuild")
  for comment in issue.get_comments():
    commenter = comment.user.login
    if not commenter in USERS_TO_TRIGGER_HOOKS: continue
    comment_msg = comment.body.encode("ascii", "ignore")
    comment_lines = [ l.strip() for l in comment_msg.split("\n") if l.strip() ][0:1]
    print "Comment first line: %s => %s" % (commenter, comment_lines)
    if not comment_lines: continue
    first_line = comment_lines[0]
    if commenter == "cmsbuild":
      if not cmdType: continue
      if match("^Command\s+"+cmdType+"\s+acknowledged.$",first_line):
        print "Acknowledged ",cmdType
        cmdType = None
      continue
    cmd = getCommentCommand(first_line)
    if not cmd: continue
    if (cmd == "ping") and cmdType: continue
    if cmd == "merge" and not pr: continue
    if not hasRights (commenter, branch, cmd, chg_files): continue
    cmdType = cmd
    print "Found: Command %s issued by %s" % (cmdType, commenter)
  if not cmdType: return True
  print "Processing ",cmdType
  if dryRun: return True
  if issue.state == "open":
    if cmdType == "merge": pr.merge()
    if cmdType == "close": issue.edit(state="closed")
  elif cmdType == "open": issue.edit(state="open")
  issue.create_comment("Command "+cmdType+" acknowledged.")
  return True

if __name__ == "__main__":
  parser = OptionParser(usage="%prog <pull-request-id>")
  parser.add_option("-n", "--dry-run",    dest="dryRun",     action="store_true", help="Do not modify Github", default=False)
  #parser.add_option("-r", "--repository", dest="repository", help="Github Repositoy name e.g. cms-sw/cmsdist.", type=str, default="cms-sw/cmsdist")
  opts, args = parser.parse_args()

  if len(args) != 1:
    parser.error("Too many/few arguments")
  prId = int(args[0])
  
  gh = Github(login_or_token=open(expanduser("~/.github-token")).read().strip())
  repo = gh.get_repo("cms-sw/cmsdist")
  if not process_pr(gh, repo, repo.get_issue(prId), opts.dryRun): exit(1)
  exit (0)
