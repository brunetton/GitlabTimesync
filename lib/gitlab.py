#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import requests


class GitlabException(Exception):
    pass


class Gitlab():

    api_version = 4
    gitlab_url = None
    private_token = None

    def __init__(self, gitlab_url: str, private_token: str):
        self.gitlab_url = gitlab_url
        self.private_token = private_token

    def add_time_entry(self, issue_id: int, time_spent_str: str):
        """Add a time entry to this issue id.
        - time_spent_str is the time spent, in Gitlab time format (ex: "30m", "1.5h", ...)
        """
        issues = self.api('GET', '/issues?iids={}'.format(issue_id))
        if len(issues) == 0:
            raise GitlabException("Can't find issue #{}".format(issue_id))
        assert len(issues) == 1, "More that one issue found with iid #{} ! For now this scripts doesn't handles multi-project. Pull requests are welcome !".format(issue_id)
        issue = issues[0]
        project_id = issue['project_id']
        answer = self.api('POST', '/projects/{}/issues/{}/add_spent_time?duration={}'.format(project_id, issue_id, time_spent_str))
        assert answer.status_code == 201
        return answer

    def api(self, method: str, endpoint: str):
        complete_url = '{}/api/v{}/{}'.format(self.gitlab_url, self.api_version, endpoint)
        headers = {'PRIVATE-TOKEN': self.private_token}
        print(complete_url)
        if method == 'GET':
            response = requests.get(complete_url, headers=headers)
            assert response.ok
            return response.json()
        elif method == 'POST':
            response = requests.post(complete_url, headers=headers)
            assert response.ok, (response.url, response.text)
            return response
        else:
            raise Exception('Method should be GET or POST')
