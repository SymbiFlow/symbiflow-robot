#!/usr/bin/env python3
import logging
import os
import re
import sys
import traceback

from github3.exceptions import ForbiddenError
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


def main():
    client = login(token=GITHUB_API_TOKEN)
    organization = client.organization(ORGANIZATION)
    repos_iterator = organization.repositories()

    info = logger.info
    debug = logger.debug

    info(f"Getting all repos in {ORGANIZATION}...")
    teams = {}
    for team in organization.teams():
        teams[team.name] = team

    if not teams['triage']:
        raise Exception("Unable to find `triage` team")
    triage_members = [x.login for x in teams['triage'].members()]
    triage_repos = [x for x in teams['triage'].repositories()]
    if not teams['committers']:
        raise Exception("Unable to find `triage` team")

    for repository in repos_iterator:
        if repository in triage_repos:
            print(f"Team triage already has {repository}")
        else:
            print(f"Adding triage to {repository}")
            teams['triage'].add_repository(repository, 'triage')

    print("Current triage_members", triage_members)
    for user in teams['committers'].members():
        if user.login not in triage_members:
            print(f'Adding {user} to triage team')
            teams['triage'].add_member(user)
        else:
            print(f'User {user} already in triage team')

    for repository in repos_iterator:
        labels = set(x.name for x in repository.labels())
        print(repository, labels)
        if 'merge-if-green' not in labels:
            try:
                repository.create_label('merge-if-green', '#00ff00', """\
Merge pull request if the CI system goes green.""")
            except ForbiddenError as e:
                print(e)


if __name__ == '__main__':
    main()
