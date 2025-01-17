# Copyright 2017 - 2018 Modoolar <info@modoolar.com>
# License LGPLv3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from .test_common import HttpTestCommon


class TestController(HttpTestCommon):
    def test_01_project_browse(self):
        self.authenticate("admin", "admin")
        response = self.url_open("/projects/" + self.project_1.key)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.url.endswith(self.get_project_url(self.project_1)), response.url
        )

    def test_02_task_browse(self):
        self.authenticate("admin", "admin")
        response = self.url_open("/tasks/" + self.task11.key)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.url.endswith(self.get_task_url(self.task11)), response.url
        )
