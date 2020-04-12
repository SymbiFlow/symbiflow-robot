#!python3
import logging
import os
import re
import sys
import traceback

from github3 import login
from github3.repos.status import Status

try:
    GITHUB_API_TOKEN = os.environ['GITHUB_API_TOKEN']
    ORGANIZATION = os.environ['ORGANIZATION']
    # PROJECT-100, [project2-900], etc
    LABEL_EXTRACTING_REGEX = os.environ.get('LABEL_EXTRACTING_REGEX',r'\s*[\[]*([a-zA-Z0-9]{2,})[-|\s][0-9]+')
except KeyError as error:
    sys.stderr.write('Please set the environment variable {0}'.format(error))
    sys.exit(1)

# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


def get_issues_that_are_prs(repository):
    # GitHub's REST API v3 considers every pull request an issue, but not every issue is a pull request.
    # For this reason, "Issues" endpoints may return both issues and pull requests in the response.
    # You can identify pull requests by the pull_request key.
    # In order to access labels we have to treat pull requests as issues
    issues_that_are_prs = []
    for issue in repository.issues(state='open', sort='created'):
        if issue.pull_request_urls:
            issues_that_are_prs.append(issue)
    return issues_that_are_prs


MISSING_PROJECT_NAME_LABEL = 'kokoro:force-run'

def label_events(issue):
    events = []
    for e in issue.events():
        if 'labeled' not in e.event:
            continue
        events.append((e.event, e.label['name']))
    return tuple(events)


def count_kokoro_label_events(label_events):
    kokoro = {'labeled': 0, 'unlabeled': 0}
    for e, l in label_events:
        if 'kokoro' in l:
            kokoro[e] += 1
    return kokoro


MAX_KOKORO_RETRIES = 3


def update_issue(client, issue):
    info = logger.info
    debug = logger.debug

    if issue.user.login != "dependabot-preview[bot]":
        return
    info(f'#{issue.number} ({issue.title}).')
    ev = label_events(issue)

    # If the PR has never had the kokoro:force-run label before, add it.
    kokoro_label_events = count_kokoro_label_events(ev)
    if kokoro_label_events['labeled'] == 0:
        info(f'#{issue.number} ({issue.title}) - Adding first kokoro:force-run.')
        issue.add_labels('kokoro:force-run')
        return

    # Get the status associated with the pull request
    pr = issue.pull_request()
    sraw = client.session.get(pr.statuses_url)
    status_events = list(reversed([Status(j, client.session) for j in sraw.json()]))
    statuses = {}
    for s in status_events:
        if s.context in statuses:
            if s.updated_at < statuses[s.context].updated_at:
                return
        statuses[s.context] = s

    users = {'kokoro-team': 0}
    failures_for_user = {'kokoro-team': 0}
    states = {'success': 0, 'pending': 0}
    for s in sorted(statuses):
        d = statuses[s]

        info(f'#{issue.number} ({issue.title}) - {d.state:10s} {s:60s} {d.creator}')
        if d.state not in states:
            states[d.state] = 0
        states[d.state] += 1

        u = d.creator.login
        if u == 'symbiflow-robot':
            u = 'kokoro-team'
        if u not in users:
            users[u] = 0
        users[u] += 1

        if d.state in ('failure', 'error'):
            if u not in failures_for_user:
                failures_for_user[u] = 0
            failures_for_user[u] += 1

    if 'kokoro-team' not in users:
        info(f'#{issue.number} ({issue.title}) - Skipping as no kokoro CI runs!')

    # Are we waiting on anything to finish?
    elif states['pending'] > 0:
        info(f"#{issue.number} ({issue.title}) - {states['pending']} pending CI jobs")

    # If there are any kokoro failures, retry.
    elif failures_for_user['kokoro-team'] > 0 or users['kokoro-team'] == 0:
        attempts = f" ({kokoro_label_events['labeled']} of {MAX_KOKORO_RETRIES}.)"
        if kokoro_label_events['labeled'] < MAX_KOKORO_RETRIES:
            info(f"#{issue.number} ({issue.title}) - Retrying Kokoro" +attempts)
            issue.add_labels('kokoro:force-run')
        else:
            info(f"#{issue.number} ({issue.title}) - Too many Kokoro failures!"+attempts)

    # If all the checks where successful, then auto-merge!
    elif states['success'] == len(statuses):
        info(f'#{issue.number} ({issue.title}) - Merging as all statuses are good!')
        pr.merge()


def manage_dependabot_pull_requests():
    client = login(token=GITHUB_API_TOKEN)
    organization = client.organization(ORGANIZATION)
    repos_iterator = organization.repositories()

    info = logger.info
    debug = logger.debug

    info(f"Getting all repos in {ORGANIZATION}...")
    for repository in repos_iterator:
        issues_that_are_prs = get_issues_that_are_prs(repository)

        info(f"Getting all PRs in {repository.full_name}...")
        for issue in issues_that_are_prs:
            try:
                update_issue(client, issue)
            except Exception as e:
                traceback.print_exc(file=sys.stdout)


if __name__ == '__main__':
    manage_dependabot_pull_requests()
