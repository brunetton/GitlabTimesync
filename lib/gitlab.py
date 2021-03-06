#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging

from . import common

log = logging.getLogger(__name__)

class GitlabException(Exception):
    pass


class Gitlab():

    api_version = 4
    gitlab_url = None
    private_token = None
    project_id = None

    def __init__(self, gitlab_url: str, project_id: int, private_token: str):
        assert gitlab_url and project_id and private_token
        self.gitlab_url = gitlab_url
        self.private_token = private_token
        self.project_id = project_id

    def add_time_entry(self, issue_id: int, time_spent_str: str):
        """Add a time entry to this issue id.
        - time_spent_str is the time spent, in Gitlab time format (ex: "30m", "1.5h", ...)
        """
        issue_id = common.str_to_int(issue_id)
        assert isinstance(issue_id, int), issue_id

        issues = self.api('GET', '/projects/{}/issues?iids={}'.format(self.project_id, issue_id))
        if len(issues) == 0:
            raise GitlabException("Can't find issue #{}".format(issue_id))
        assert len(issues) == 1, "More that one issue found with iid #{} ! For now this scripts doesn't handles multi-project. Pull requests are welcome !".format(issue_id)
        answer = self.api('POST', '/projects/{}/issues/{}/add_spent_time?duration={}'.format(self.project_id, issue_id, time_spent_str))
        assert answer.status_code == 201
        return answer

    def api(self, method: str, endpoint: str):
        complete_url = '{}/api/v{}/{}'.format(self.gitlab_url, self.api_version, endpoint)
        log.debug(complete_url)
        headers = {'PRIVATE-TOKEN': self.private_token}
        if method == 'GET':
            response = requests.get(complete_url, headers=headers)
            assert response.ok, (response.url, response.text)
            return response.json()
        elif method == 'POST':
            response = requests.post(complete_url, headers=headers)
            assert response.ok, (response.url, response.text)
            return response
        else:
            raise Exception('Method should be GET or POST')
