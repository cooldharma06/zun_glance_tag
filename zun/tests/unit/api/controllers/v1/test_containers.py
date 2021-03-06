# Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import mock
from mock import patch
from webtest.app import AppError

from oslo_utils import uuidutils

from zun.common import consts
from zun.common import exception
from zun import objects
from zun.tests.unit.api import base as api_base
from zun.tests.unit.db import utils
from zun.tests.unit.objects import utils as obj_utils

CURRENT_VERSION = "container 1.6"


class TestContainerController(api_base.FunctionalTest):
    @patch('zun.network.neutron.NeutronAPI.get_available_network')
    @patch('zun.compute.api.API.container_run')
    @patch('zun.compute.api.API.image_search')
    def test_run_container(self, mock_search, mock_container_run,
                           mock_neutron_get_network):
        mock_container_run.side_effect = lambda x, y, z, v: y

        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512",'
                  '"environment": {"key1": "val1", "key2": "val2"}}')

        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post('/v1/containers?run=true',
                                 params=params,
                                 headers=headers,
                                 content_type='application/json')

        self.assertEqual(202, response.status_int)
        self.assertTrue(mock_container_run.called)
        mock_neutron_get_network.assert_called_once()

    @patch('zun.compute.api.API.container_run')
    @patch('zun.compute.api.API.image_search')
    def test_run_container_wrong_run_value(self, mock_search,
                                           mock_container_run):
        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512",'
                  '"environment": {"key1": "val1", "key2": "val2"}}')
        with self.assertRaisesRegex(AppError,
                                    "Invalid input for query parameters"):
            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            self.app.post('/v1/containers?run=xyz', params=params,
                          content_type='application/json', headers=headers)

    @patch('zun.network.neutron.NeutronAPI.get_available_network')
    @patch('zun.compute.api.API.container_run')
    @patch('zun.compute.api.API.image_search')
    def test_run_container_runtime(self, mock_search,
                                   mock_container_run,
                                   mock_neutron_get_network):
        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512",'
                  '"environment": {"key1": "val1", "key2": "val2"},'
                  '"runtime": "runc"}')
        api_version = {"OpenStack-API-Version": CURRENT_VERSION}
        response = self.app.post('/v1/containers?run=true',
                                 params=params,
                                 content_type='application/json',
                                 headers=api_version)

        self.assertEqual(202, response.status_int)
        self.assertTrue(mock_container_run.called)
        mock_neutron_get_network.assert_called_once()

    def test_run_container_runtime_wrong_api_version(self):
        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512",'
                  '"environment": {"key1": "val1", "key2": "val2"},'
                  '"runtime": "runc"}')
        headers = {"OpenStack-API-Version": "container 1.4",
                   "Accept": "application/json"}
        with self.assertRaisesRegex(AppError,
                                    "Invalid param runtime"):
            self.app.post('/v1/containers?run=true',
                          params=params, content_type='application/json',
                          headers=headers)

    def test_run_container_runtime_wrong_value(self):
        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512",'
                  '"environment": {"key1": "val1", "key2": "val2"},'
                  '"runtime": "wrong_value"}')
        api_version = {"OpenStack-API-Version": CURRENT_VERSION}
        with self.assertRaisesRegex(AppError,
                                    "Invalid input for field"):
            self.app.post('/v1/containers?run=true',
                          params=params, content_type='application/json',
                          headers=api_version)

    @patch('zun.network.neutron.NeutronAPI.get_available_network')
    @patch('zun.compute.api.API.container_run')
    @patch('zun.compute.api.API.image_search')
    def test_run_container_with_false(self, mock_search,
                                      mock_container_run,
                                      mock_neutron_get_network):
        mock_container_run.side_effect = lambda x, y, z, v: y

        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512",'
                  '"environment": {"key1": "val1", "key2": "val2"}}')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post('/v1/containers?run=false',
                                 params=params,
                                 content_type='application/json',
                                 headers=headers)
        self.assertEqual(202, response.status_int)
        self.assertFalse(mock_container_run.called)
        mock_neutron_get_network.assert_called_once()

    @patch('zun.compute.api.API.container_run')
    @patch('zun.compute.api.API.image_search')
    def test_run_container_with_wrong(self, mock_search,
                                      mock_container_run):
        mock_container_run.side_effect = exception.InvalidValue
        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512",'
                  '"environment": {"key1": "val1", "key2": "val2"}}')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        self.assertRaises(AppError, self.app.post, '/v1/containers?run=wrong',
                          params=params, content_type='application/json',
                          headers=headers)
        self.assertTrue(mock_container_run.not_called)

    @patch('zun.network.neutron.NeutronAPI.get_available_network')
    @patch('zun.compute.api.API.container_create')
    @patch('zun.compute.api.API.image_search')
    def test_create_container(self, mock_search, mock_container_create,
                              mock_neutron_get_network):
        mock_container_create.side_effect = lambda x, y, z, v: y

        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512",'
                  '"environment": {"key1": "val1", "key2": "val2"}}')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post('/v1/containers/',
                                 params=params, headers=headers,
                                 content_type='application/json')

        self.assertEqual(202, response.status_int)
        self.assertTrue(mock_container_create.called)
        mock_neutron_get_network.assert_called_once()

    @patch('zun.compute.api.API.container_create')
    def test_create_container_image_not_specified(self, mock_container_create):

        params = ('{"name": "MyDocker",'
                  '"command": "env", "memory": "512",'
                  '"environment": {"key1": "val1", "key2": "val2"}}')
        with self.assertRaisesRegex(AppError,
                                    "is a required property"):
            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            self.app.post('/v1/containers/',
                          params=params, headers=headers,
                          content_type='application/json')
        self.assertTrue(mock_container_create.not_called)

    @patch('zun.network.neutron.NeutronAPI.get_available_network')
    @patch('zun.compute.api.API.container_create')
    @patch('zun.compute.api.API.image_search')
    def test_create_container_image_not_found(self, mock_search,
                                              mock_container_create,
                                              mock_neutron_get_network):
        mock_container_create.side_effect = lambda x, y, z, v: y
        mock_search.side_effect = exception.ImageNotFound()

        params = {"name": "MyDocker", "image": "not-found"}
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.post_json('/containers/', params, headers=headers,
                                  expect_errors=True)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(404, response.status_int)
        self.assertFalse(mock_container_create.called)
        mock_neutron_get_network.assert_called_once()

    @patch('zun.network.neutron.NeutronAPI.get_available_network')
    @patch('zun.compute.api.API.container_create')
    @patch('zun.compute.api.API.image_search')
    def test_create_container_set_project_id_and_user_id(
            self, mock_search, mock_container_create,
            mock_neutron_get_network):
        def _create_side_effect(cnxt, container, extra_spec, networks):
            self.assertEqual(self.context.project_id, container.project_id)
            self.assertEqual(self.context.user_id, container.user_id)
            return container
        mock_container_create.side_effect = _create_side_effect

        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512",'
                  '"environment": {"key1": "val1", "key2": "val2"}}')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        self.app.post('/v1/containers/',
                      params=params, headers=headers,
                      content_type='application/json')
        mock_neutron_get_network.assert_called_once()

    @patch('zun.network.neutron.NeutronAPI.get_available_network')
    @patch('zun.compute.api.API.container_create')
    @patch('zun.compute.api.API.image_search')
    def test_create_container_resp_has_status_reason(self, mock_search,
                                                     mock_container_create,
                                                     mock_neutron_get_network):
        mock_container_create.side_effect = lambda x, y, z, v: y
        # Create a container with a command
        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512",'
                  '"environment": {"key1": "val1", "key2": "val2"}}')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post('/v1/containers/',
                                 params=params, headers=headers,
                                 content_type='application/json')
        self.assertEqual(202, response.status_int)
        self.assertIn('status_reason', response.json.keys())
        mock_neutron_get_network.assert_called_once()

    @patch('zun.network.neutron.NeutronAPI.get_available_network')
    @patch('zun.compute.api.API.container_show')
    @patch('zun.compute.api.API.container_create')
    @patch('zun.compute.api.API.container_delete')
    @patch('zun.compute.api.API.image_search')
    def test_create_container_with_command(self, mock_search,
                                           mock_container_delete,
                                           mock_container_create,
                                           mock_container_show,
                                           mock_neutron_get_network):
        mock_container_create.side_effect = lambda x, y, z, v: y
        fake_network = {'id': 'foo'}
        mock_neutron_get_network.return_value = fake_network
        # Create a container with a command
        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512",'
                  '"environment": {"key1": "val1", "key2": "val2"}}')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post('/v1/containers/',
                                 params=params, headers=headers,
                                 content_type='application/json')
        self.assertEqual(202, response.status_int)
        # get all containers
        container = objects.Container.list(self.context)[0]
        container.status = 'Stopped'
        mock_container_show.return_value = container
        response = self.app.get('/v1/containers/')
        self.assertEqual(200, response.status_int)
        self.assertEqual(2, len(response.json))
        c = response.json['containers'][0]
        self.assertIsNotNone(c.get('uuid'))
        self.assertEqual('MyDocker', c.get('name'))
        self.assertEqual('env', c.get('command'))
        self.assertEqual('Stopped', c.get('status'))
        self.assertEqual('512M', c.get('memory'))
        self.assertEqual({"key1": "val1", "key2": "val2"},
                         c.get('environment'))
        requested_networks = mock_container_create.call_args[0][3]
        self.assertEqual(1, len(requested_networks))
        self.assertEqual(fake_network['id'], requested_networks[0]['network'])

        def side_effect(*args, **kwargs):
            (ctx, cnt, force) = args
            cnt.destroy(ctx)

        # Delete the container we created
        mock_container_delete.side_effect = side_effect
        response = self.app.delete(
            '/v1/containers/%s?force=True' % c.get('uuid'))
        self.assertEqual(204, response.status_int)

        response = self.app.get('/v1/containers/')
        self.assertEqual(200, response.status_int)
        c = response.json['containers']
        self.assertEqual(0, len(c))
        self.assertTrue(mock_container_create.called)
        mock_neutron_get_network.assert_called_once()

    @patch('zun.network.neutron.NeutronAPI.get_available_network')
    @patch('zun.compute.api.API.container_show')
    @patch('zun.compute.api.API.container_create')
    @patch('zun.compute.api.API.image_search')
    def test_create_container_without_memory(self, mock_search,
                                             mock_container_create,
                                             mock_container_show,
                                             mock_neutron_get_network):
        mock_container_create.side_effect = lambda x, y, z, v: y
        fake_network = {'id': 'foo'}
        mock_neutron_get_network.return_value = fake_network
        # Create a container with a command
        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env",'
                  '"environment": {"key1": "val1", "key2": "val2"}}')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post('/v1/containers/',
                                 params=params, headers=headers,
                                 content_type='application/json')
        self.assertEqual(202, response.status_int)
        # get all containers
        container = objects.Container.list(self.context)[0]
        container.status = 'Stopped'
        mock_container_show.return_value = container
        response = self.app.get('/v1/containers/')
        self.assertEqual(200, response.status_int)
        self.assertEqual(2, len(response.json))
        c = response.json['containers'][0]
        self.assertIsNotNone(c.get('uuid'))
        self.assertEqual('MyDocker', c.get('name'))
        self.assertEqual('env', c.get('command'))
        self.assertEqual('Stopped', c.get('status'))
        self.assertIsNone(c.get('memory'))
        self.assertEqual({"key1": "val1", "key2": "val2"},
                         c.get('environment'))
        mock_neutron_get_network.assert_called_once()
        requested_networks = mock_container_create.call_args[0][3]
        self.assertEqual(1, len(requested_networks))
        self.assertEqual(fake_network['id'], requested_networks[0]['network'])

    @patch('zun.network.neutron.NeutronAPI.get_available_network')
    @patch('zun.compute.api.API.container_show')
    @patch('zun.compute.api.API.container_create')
    @patch('zun.compute.api.API.image_search')
    def test_create_container_without_environment(self, mock_search,
                                                  mock_container_create,
                                                  mock_container_show,
                                                  mock_neutron_get_network):
        mock_container_create.side_effect = lambda x, y, z, v: y
        fake_network = {'id': 'foo'}
        mock_neutron_get_network.return_value = fake_network
        # Create a container with a command
        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512"}')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post('/v1/containers/',
                                 params=params, headers=headers,
                                 content_type='application/json')
        self.assertEqual(202, response.status_int)
        # get all containers
        container = objects.Container.list(self.context)[0]
        container.status = 'Stopped'
        mock_container_show.return_value = container
        response = self.app.get('/v1/containers/')
        self.assertEqual(200, response.status_int)
        self.assertEqual(2, len(response.json))
        c = response.json['containers'][0]
        self.assertIsNotNone(c.get('uuid'))
        self.assertEqual('MyDocker', c.get('name'))
        self.assertEqual('env', c.get('command'))
        self.assertEqual('Stopped', c.get('status'))
        self.assertEqual('512M', c.get('memory'))
        self.assertEqual({}, c.get('environment'))
        mock_neutron_get_network.assert_called_once()
        requested_networks = mock_container_create.call_args[0][3]
        self.assertEqual(1, len(requested_networks))
        self.assertEqual(fake_network['id'], requested_networks[0]['network'])

    @patch('zun.network.neutron.NeutronAPI.get_available_network')
    @patch('zun.compute.api.API.container_show')
    @patch('zun.compute.api.API.container_create')
    @patch('zun.compute.api.API.image_search')
    def test_create_container_without_name(self, mock_search,
                                           mock_container_create,
                                           mock_container_show,
                                           mock_neutron_get_network):
        # No name param
        mock_container_create.side_effect = lambda x, y, z, v: y
        fake_network = {'id': 'foo'}
        mock_neutron_get_network.return_value = fake_network
        params = ('{"image": "ubuntu", "command": "env", "memory": "512",'
                  '"environment": {"key1": "val1", "key2": "val2"}}')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post('/v1/containers/',
                                 params=params, headers=headers,
                                 content_type='application/json')
        self.assertEqual(202, response.status_int)
        # get all containers
        container = objects.Container.list(self.context)[0]
        container.status = 'Stopped'
        mock_container_show.return_value = container
        response = self.app.get('/v1/containers/')
        self.assertEqual(200, response.status_int)
        self.assertEqual(2, len(response.json))
        c = response.json['containers'][0]
        self.assertIsNotNone(c.get('uuid'))
        self.assertIsNotNone(c.get('name'))
        self.assertEqual('env', c.get('command'))
        self.assertEqual('Stopped', c.get('status'))
        self.assertEqual('512M', c.get('memory'))
        self.assertEqual({"key1": "val1", "key2": "val2"},
                         c.get('environment'))
        mock_neutron_get_network.assert_called_once()
        requested_networks = mock_container_create.call_args[0][3]
        self.assertEqual(1, len(requested_networks))
        self.assertEqual(fake_network['id'], requested_networks[0]['network'])

    @patch('zun.network.neutron.NeutronAPI.get_available_network')
    @patch('zun.compute.api.API.container_show')
    @patch('zun.compute.api.API.container_create')
    @patch('zun.compute.api.API.image_search')
    def test_create_container_with_restart_policy_no_retry_0(
            self,
            mock_search,
            mock_container_create,
            mock_container_show,
            mock_neutron_get_network):
        mock_container_create.side_effect = lambda x, y, z, v: y
        fake_network = {'id': 'foo'}
        mock_neutron_get_network.return_value = fake_network
        # Create a container with a command
        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512",'
                  '"restart_policy": {"Name": "no",'
                  '"MaximumRetryCount": "0"}}')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post('/v1/containers/',
                                 params=params, headers=headers,
                                 content_type='application/json')
        self.assertEqual(202, response.status_int)
        # get all containers
        container = objects.Container.list(self.context)[0]
        container.status = 'Stopped'
        mock_container_show.return_value = container
        response = self.app.get('/v1/containers/')
        self.assertEqual(200, response.status_int)
        self.assertEqual(2, len(response.json))
        c = response.json['containers'][0]
        self.assertIsNotNone(c.get('uuid'))
        self.assertEqual('MyDocker', c.get('name'))
        self.assertEqual('env', c.get('command'))
        self.assertEqual('Stopped', c.get('status'))
        self.assertEqual('512M', c.get('memory'))
        self.assertEqual({"Name": "no", "MaximumRetryCount": "0"},
                         c.get('restart_policy'))
        mock_neutron_get_network.assert_called_once()
        requested_networks = mock_container_create.call_args[0][3]
        self.assertEqual(1, len(requested_networks))
        self.assertEqual(fake_network['id'], requested_networks[0]['network'])

    @patch('zun.network.neutron.NeutronAPI.get_available_network')
    @patch('zun.compute.api.API.container_show')
    @patch('zun.compute.api.API.container_create')
    @patch('zun.compute.api.API.image_search')
    def test_create_container_with_restart_policy_no_retry_6(
            self,
            mock_search,
            mock_container_create,
            mock_container_show,
            mock_neutron_get_network):
        mock_container_create.side_effect = lambda x, y, z, v: y
        fake_network = {'id': 'foo'}
        mock_neutron_get_network.return_value = fake_network
        # Create a container with a command
        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512",'
                  '"restart_policy": {"Name": "no",'
                  '"MaximumRetryCount": "6"}}')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post('/v1/containers/',
                                 params=params, headers=headers,
                                 content_type='application/json')
        self.assertEqual(202, response.status_int)
        # get all containers
        container = objects.Container.list(self.context)[0]
        container.status = 'Stopped'
        mock_container_show.return_value = container
        response = self.app.get('/v1/containers/')
        self.assertEqual(200, response.status_int)
        self.assertEqual(2, len(response.json))
        c = response.json['containers'][0]
        self.assertIsNotNone(c.get('uuid'))
        self.assertEqual('MyDocker', c.get('name'))
        self.assertEqual('env', c.get('command'))
        self.assertEqual('Stopped', c.get('status'))
        self.assertEqual('512M', c.get('memory'))
        self.assertEqual({"Name": "no", "MaximumRetryCount": "0"},
                         c.get('restart_policy'))
        mock_neutron_get_network.assert_called_once()
        requested_networks = mock_container_create.call_args[0][3]
        self.assertEqual(1, len(requested_networks))
        self.assertEqual(fake_network['id'], requested_networks[0]['network'])

    @patch('zun.network.neutron.NeutronAPI.get_available_network')
    @patch('zun.compute.api.API.container_show')
    @patch('zun.compute.api.API.container_create')
    @patch('zun.compute.api.API.image_search')
    def test_create_container_with_restart_policy_miss_retry(
            self,
            mock_search,
            mock_container_create,
            mock_container_show,
            mock_neutron_get_network):
        mock_container_create.side_effect = lambda x, y, z, v: y
        fake_network = {'id': 'foo'}
        mock_neutron_get_network.return_value = fake_network
        # Create a container with a command
        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512",'
                  '"restart_policy": {"Name": "no"}}')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post('/v1/containers/',
                                 params=params, headers=headers,
                                 content_type='application/json')
        self.assertEqual(202, response.status_int)
        # get all containers
        container = objects.Container.list(self.context)[0]
        container.status = 'Stopped'
        mock_container_show.return_value = container
        response = self.app.get('/v1/containers/')
        self.assertEqual(200, response.status_int)
        self.assertEqual(2, len(response.json))
        c = response.json['containers'][0]
        self.assertIsNotNone(c.get('uuid'))
        self.assertEqual('MyDocker', c.get('name'))
        self.assertEqual('env', c.get('command'))
        self.assertEqual('Stopped', c.get('status'))
        self.assertEqual('512M', c.get('memory'))
        self.assertEqual({"Name": "no", "MaximumRetryCount": "0"},
                         c.get('restart_policy'))
        mock_neutron_get_network.assert_called_once()
        requested_networks = mock_container_create.call_args[0][3]
        self.assertEqual(1, len(requested_networks))
        self.assertEqual(fake_network['id'], requested_networks[0]['network'])

    @patch('zun.network.neutron.NeutronAPI.get_available_network')
    @patch('zun.compute.api.API.container_show')
    @patch('zun.compute.api.API.container_create')
    @patch('zun.compute.api.API.image_search')
    def test_create_container_with_restart_policy_unless_stopped(
            self,
            mock_search,
            mock_container_create,
            mock_container_show,
            mock_neutron_get_network):
        mock_container_create.side_effect = lambda x, y, z, v: y
        fake_network = {'id': 'foo'}
        mock_neutron_get_network.return_value = fake_network
        # Create a container with a command
        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512",'
                  '"restart_policy": {"Name": "unless-stopped",'
                  '"MaximumRetryCount": "0"}}')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post('/v1/containers/',
                                 params=params, headers=headers,
                                 content_type='application/json')
        self.assertEqual(202, response.status_int)
        # get all containers
        container = objects.Container.list(self.context)[0]
        container.status = 'Stopped'
        mock_container_show.return_value = container
        response = self.app.get('/v1/containers/')
        self.assertEqual(200, response.status_int)
        self.assertEqual(2, len(response.json))
        c = response.json['containers'][0]
        self.assertIsNotNone(c.get('uuid'))
        self.assertEqual('MyDocker', c.get('name'))
        self.assertEqual('env', c.get('command'))
        self.assertEqual('Stopped', c.get('status'))
        self.assertEqual('512M', c.get('memory'))
        self.assertEqual({"Name": "unless-stopped", "MaximumRetryCount": "0"},
                         c.get('restart_policy'))
        mock_neutron_get_network.assert_called_once()
        requested_networks = mock_container_create.call_args[0][3]
        self.assertEqual(1, len(requested_networks))
        self.assertEqual(fake_network['id'], requested_networks[0]['network'])

    @patch('zun.network.neutron.NeutronAPI.get_neutron_port')
    @patch('zun.network.neutron.NeutronAPI.ensure_neutron_port_usable')
    @patch('zun.compute.api.API.container_show')
    @patch('zun.compute.api.API.container_create')
    @patch('zun.compute.api.API.container_delete')
    @patch('zun.compute.api.API.image_search')
    def test_create_container_with_requested_neutron_port(
            self, mock_search, mock_container_delete, mock_container_create,
            mock_container_show, mock_ensure_port_usable, mock_get_port):
        mock_container_create.side_effect = lambda x, y, z, v: y
        fake_port = {'network_id': 'foo', 'id': 'bar'}
        mock_get_port.return_value = fake_port
        # Create a container with a command
        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512",'
                  '"environment": {"key1": "val1", "key2": "val2"},'
                  '"nets": [{"port": "testport"}]}')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post('/v1/containers/',
                                 params=params, headers=headers,
                                 content_type='application/json')
        self.assertEqual(202, response.status_int)
        # get all containers
        container = objects.Container.list(self.context)[0]
        container.status = 'Stopped'
        mock_container_show.return_value = container
        response = self.app.get('/v1/containers/')
        self.assertEqual(200, response.status_int)
        self.assertEqual(2, len(response.json))
        c = response.json['containers'][0]
        self.assertIsNotNone(c.get('uuid'))
        self.assertEqual('MyDocker', c.get('name'))
        self.assertEqual('env', c.get('command'))
        self.assertEqual('Stopped', c.get('status'))
        self.assertEqual('512M', c.get('memory'))
        self.assertEqual({"key1": "val1", "key2": "val2"},
                         c.get('environment'))
        requested_networks = mock_container_create.call_args[0][3]
        self.assertEqual(1, len(requested_networks))
        self.assertEqual(fake_port['network_id'],
                         requested_networks[0]['network'])
        self.assertEqual(fake_port['id'], requested_networks[0]['port'])

        def side_effect(*args, **kwargs):
            (ctx, cnt, force) = args
            cnt.destroy(ctx)

        # Delete the container we created
        mock_container_delete.side_effect = side_effect
        response = self.app.delete(
            '/v1/containers/%s?force=True' % c.get('uuid'))
        self.assertEqual(204, response.status_int)

        response = self.app.get('/v1/containers/')
        self.assertEqual(200, response.status_int)
        c = response.json['containers']
        self.assertEqual(0, len(c))
        self.assertTrue(mock_container_create.called)

    @patch('zun.network.neutron.NeutronAPI.get_available_network')
    @patch('zun.compute.api.API.container_show')
    @patch('zun.compute.api.API.container_create')
    @patch('zun.compute.api.API.image_search')
    def test_create_container_with_restart_policy_always_and_retrycount(
            self,
            mock_search,
            mock_container_create,
            mock_container_show,
            mock_neutron_get_network):
        mock_container_create.side_effect = lambda x, y, z, v: y
        # Create a container with a command
        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512",'
                  '"restart_policy": {"Name": "always",'
                  '"MaximumRetryCount": "1"}}')
        with self.assertRaisesRegex(
                AppError, "maximum retry count not valid with"):
            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            self.app.post('/v1/containers/',
                          params=params, headers=headers,
                          content_type='application/json')
        self.assertTrue(mock_container_create.not_called)
        mock_neutron_get_network.assert_called_once()

    @patch('zun.compute.api.API.container_create')
    @patch('zun.compute.api.API.image_search')
    def test_create_container_invalid_long_name(self, mock_search,
                                                mock_container_create):
        # Long name
        params = ('{"name": "' + 'i' * 256 + '", "image": "ubuntu",'
                  '"command": "env", "memory": "512"}')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        self.assertRaises(AppError, self.app.post, '/v1/containers/',
                          params=params, content_type='application/json',
                          headers=headers)
        self.assertTrue(mock_container_create.not_called)

    @patch('zun.compute.api.API.container_show')
    @patch('zun.objects.Container.list')
    def test_get_all_containers(self, mock_container_list,
                                mock_container_show):
        test_container = utils.get_test_container()
        containers = [objects.Container(self.context, **test_container)]
        mock_container_list.return_value = containers
        mock_container_show.return_value = containers[0]

        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.get('/v1/containers/', headers=headers)

        mock_container_list.assert_called_once_with(mock.ANY,
                                                    1000, None, 'id', 'asc',
                                                    filters=None)
        context = mock_container_list.call_args[0][0]
        self.assertIs(False, context.all_tenants)
        self.assertEqual(200, response.status_int)
        actual_containers = response.json['containers']
        self.assertEqual(1, len(actual_containers))
        self.assertEqual(test_container['uuid'],
                         actual_containers[0].get('uuid'))

    @patch('zun.compute.api.API.container_show')
    @patch('zun.objects.Container.list')
    def test_get_all_containers_all_tenants(self, mock_container_list,
                                            mock_container_show):
        test_container = utils.get_test_container()
        containers = [objects.Container(self.context, **test_container)]
        mock_container_list.return_value = containers
        mock_container_show.return_value = containers[0]

        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.get('/v1/containers/?all_tenants=1',
                                headers=headers)

        mock_container_list.assert_called_once_with(mock.ANY,
                                                    1000, None, 'id', 'asc',
                                                    filters=None)
        context = mock_container_list.call_args[0][0]
        self.assertIs(True, context.all_tenants)
        self.assertEqual(200, response.status_int)
        actual_containers = response.json['containers']
        self.assertEqual(1, len(actual_containers))
        self.assertEqual(test_container['uuid'],
                         actual_containers[0].get('uuid'))

    @patch('zun.compute.api.API.container_show')
    @patch('zun.objects.Container.list')
    def test_get_all_has_status_reason_and_image_pull_policy(
            self, mock_container_list, mock_container_show):
        test_container = utils.get_test_container()
        containers = [objects.Container(self.context, **test_container)]
        mock_container_list.return_value = containers
        mock_container_show.return_value = containers[0]

        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.get('/v1/containers/', headers=headers)
        self.assertEqual(200, response.status_int)
        actual_containers = response.json['containers']
        self.assertEqual(1, len(actual_containers))
        self.assertEqual(test_container['uuid'],
                         actual_containers[0].get('uuid'))
        self.assertIn('status_reason', actual_containers[0].keys())
        self.assertIn('image_pull_policy', actual_containers[0].keys())

    @patch('zun.compute.api.API.container_show')
    @patch('zun.objects.Container.list')
    def test_get_all_containers_with_pagination_marker(self,
                                                       mock_container_list,
                                                       mock_container_show):
        container_list = []
        for id_ in range(4):
            test_container = utils.create_test_container(
                id=id_, uuid=uuidutils.generate_uuid(),
                name='container' + str(id_), context=self.context)
            container_list.append(objects.Container(self.context,
                                                    **test_container))
        mock_container_list.return_value = container_list[-1:]
        mock_container_show.return_value = container_list[-1]
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.get('/v1/containers/?limit=3&marker=%s'
                                % container_list[2].uuid, headers=headers)

        self.assertEqual(200, response.status_int)
        actual_containers = response.json['containers']
        self.assertEqual(1, len(actual_containers))
        self.assertEqual(container_list[-1].uuid,
                         actual_containers[0].get('uuid'))

    @patch('zun.compute.api.API.container_show')
    @patch('zun.objects.Container.list')
    def test_get_all_containers_with_exception(self, mock_container_list,
                                               mock_container_show):
        test_container = utils.get_test_container()
        containers = [objects.Container(self.context, **test_container)]
        mock_container_list.return_value = containers
        mock_container_show.side_effect = Exception

        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.get('/v1/containers/', headers=headers)

        mock_container_list.assert_called_once_with(mock.ANY,
                                                    1000, None, 'id', 'asc',
                                                    filters=None)
        self.assertEqual(200, response.status_int)
        actual_containers = response.json['containers']
        self.assertEqual(1, len(actual_containers))
        self.assertEqual(test_container['uuid'],
                         actual_containers[0].get('uuid'))

        self.assertEqual(consts.UNKNOWN,
                         actual_containers[0].get('status'))

    @patch('zun.compute.api.API.container_show')
    @patch('zun.objects.Container.get_by_uuid')
    def test_get_one_by_uuid(self, mock_container_get_by_uuid,
                             mock_container_show):
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_container_get_by_uuid.return_value = test_container_obj
        mock_container_show.return_value = test_container_obj

        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.get('/v1/containers/%s/' % test_container['uuid'],
                                headers=headers)

        mock_container_get_by_uuid.assert_called_once_with(
            mock.ANY,
            test_container['uuid'])
        context = mock_container_get_by_uuid.call_args[0][0]
        self.assertIs(False, context.all_tenants)
        self.assertEqual(200, response.status_int)
        self.assertEqual(test_container['uuid'],
                         response.json['uuid'])

    @patch('zun.compute.api.API.container_show')
    @patch('zun.objects.Container.get_by_uuid')
    def test_get_one_by_uuid_all_tenants(self, mock_container_get_by_uuid,
                                         mock_container_show):
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_container_get_by_uuid.return_value = test_container_obj
        mock_container_show.return_value = test_container_obj

        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.get('/v1/containers/%s/?all_tenants=1' %
                                test_container['uuid'], headers=headers)

        mock_container_get_by_uuid.assert_called_once_with(
            mock.ANY,
            test_container['uuid'])
        context = mock_container_get_by_uuid.call_args[0][0]
        self.assertIs(True, context.all_tenants)
        self.assertEqual(200, response.status_int)
        self.assertEqual(test_container['uuid'],
                         response.json['uuid'])

    @patch('zun.compute.api.API.container_update')
    @patch('zun.objects.Container.get_by_uuid')
    def test_patch_by_uuid(self, mock_container_get_by_uuid, mock_update):
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_container_get_by_uuid.return_value = test_container_obj
        mock_update.return_value = test_container_obj

        params = {'cpu': 1}
        container_uuid = test_container.get('uuid')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.patch_json(
            '/v1/containers/%s/' % container_uuid,
            params=params, headers=headers)

        self.assertEqual(200, response.status_int)
        self.assertTrue(mock_update.called)

    def _action_test(self, container, action, ident_field,
                     mock_container_action, status_code, query_param=''):
        test_container_obj = objects.Container(self.context, **container)
        ident = container.get(ident_field)
        get_by_ident_loc = 'zun.objects.Container.get_by_%s' % ident_field
        with patch(get_by_ident_loc) as mock_get_by_indent:
            mock_get_by_indent.return_value = test_container_obj
            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            response = self.app.post('/v1/containers/%s/%s/?%s' %
                                     (ident, action, query_param),
                                     headers=headers)
            self.assertEqual(status_code, response.status_int)

            # Only PUT should work, others like GET should fail
            self.assertRaises(AppError, self.app.get,
                              ('/v1/containers/%s/%s/' %
                               (ident, action)), headers=headers)
        if query_param:
            value = query_param.split('=')[1]
            mock_container_action.assert_called_once_with(
                mock.ANY, test_container_obj, value)
        else:
            mock_container_action.assert_called_once_with(
                mock.ANY, test_container_obj)

    @patch('zun.objects.Container.get_by_uuid')
    def test_rename_by_uuid(self, mock_container_get_by_uuid):
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_container_get_by_uuid.return_value = test_container_obj

        with patch.object(test_container_obj, 'save') as mock_save:
            params = {'name': 'new_name'}
            container_uuid = test_container.get('uuid')
            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            response = self.app.post('/v1/containers/%s/rename' %
                                     container_uuid, params=params,
                                     headers=headers)

            mock_save.assert_called_once()
            self.assertEqual(200, response.status_int)
            self.assertEqual('new_name', test_container_obj.name)

    @patch('zun.objects.Container.get_by_uuid')
    def test_rename_with_old_name_by_uuid(self, mock_container_get_by_uuid):
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_container_get_by_uuid.return_value = test_container_obj
        container_uuid = test_container.get('uuid')
        container_name = test_container.get('name')

        params = {'name': container_name}
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        self.assertRaises(AppError, self.app.post,
                          '/v1/containers/%s/rename' %
                          container_uuid, params=params, headers=headers)

    @patch('zun.objects.Container.get_by_name')
    def test_rename_with_invalid_name_by_uuid(self,
                                              mock_container_get_by_uuid):
        invalid_names = ['a@', 'a', "", '*' * 265, " ", "     ", "a b", 'ab@']
        for value in invalid_names:
            test_container = utils.get_test_container()
            test_container_obj = \
                objects.Container(self.context, **test_container)
            mock_container_get_by_uuid.return_value = test_container_obj
            container_uuid = test_container.get('uuid')

            params = {'name': value}
            with self.assertRaisesRegex(AppError,
                                        "Invalid input for query parameters"):
                headers = {'OpenStack-API-Version': CURRENT_VERSION}
                self.app.post('/v1/containers/%s/rename' %
                              container_uuid, params=params, headers=headers)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_start')
    def test_start_by_uuid(self, mock_container_start, mock_validate):
        test_container_obj = objects.Container(self.context,
                                               **utils.get_test_container())
        mock_container_start.return_value = test_container_obj
        test_container = utils.get_test_container()
        self._action_test(test_container, 'start', 'uuid',
                          mock_container_start, 202)

    def test_start_by_uuid_invalid_state(self):
        uuid = uuidutils.generate_uuid()
        test_object = utils.create_test_container(context=self.context,
                                                  uuid=uuid, status='Running')
        with self.assertRaisesRegex(
                AppError, "Cannot start container %s in Running state" % uuid):
            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            self.app.post('/v1/containers/%s/%s/' % (test_object.uuid,
                                                     'start'), headers=headers)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_stop')
    def test_stop_by_uuid(self, mock_container_stop, mock_validate):
        test_container_obj = objects.Container(self.context,
                                               **utils.get_test_container())
        mock_container_stop.return_value = test_container_obj
        test_container = utils.get_test_container()
        self._action_test(test_container, 'stop', 'uuid',
                          mock_container_stop, 202,
                          query_param='timeout=10')

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_stop')
    def test_stop_by_name_invalid_timeout_value(self,
                                                mock_container_stop,
                                                mock_validate):
        test_container = utils.get_test_container()
        with self.assertRaisesRegex(AppError,
                                    "Invalid input for query parameters"):
            self._action_test(test_container, 'stop', 'name',
                              mock_container_stop, 202,
                              query_param='timeout=xyz')

    def test_stop_by_uuid_invalid_state(self):
        uuid = uuidutils.generate_uuid()
        test_object = utils.create_test_container(context=self.context,
                                                  uuid=uuid, status='Stopped')
        with self.assertRaisesRegex(
                AppError, "Cannot stop container %s in Stopped state" % uuid):
            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            self.app.post('/v1/containers/%s/%s/' % (test_object.uuid,
                                                     'stop'), headers=headers)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_pause')
    def test_pause_by_uuid(self, mock_container_pause, mock_validate):
        test_container_obj = objects.Container(self.context,
                                               **utils.get_test_container())
        mock_container_pause.return_value = test_container_obj
        test_container = utils.get_test_container()
        self._action_test(test_container, 'pause', 'uuid',
                          mock_container_pause, 202)

    def test_pause_by_uuid_invalid_state(self):
        uuid = uuidutils.generate_uuid()
        test_object = utils.create_test_container(context=self.context,
                                                  uuid=uuid, status='Stopped')
        with self.assertRaisesRegex(
                AppError, "Cannot pause container %s in Stopped state" % uuid):
            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            self.app.post('/v1/containers/%s/%s/' % (test_object.uuid,
                                                     'pause'), headers=headers)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_unpause')
    def test_unpause_by_uuid(self, mock_container_unpause, mock_validate):
        test_container_obj = objects.Container(self.context,
                                               **utils.get_test_container())
        mock_container_unpause.return_value = test_container_obj
        test_container = utils.get_test_container()
        self._action_test(test_container, 'unpause', 'uuid',
                          mock_container_unpause, 202)

    def test_unpause_by_uuid_invalid_state(self):
        uuid = uuidutils.generate_uuid()
        test_object = utils.create_test_container(context=self.context,
                                                  uuid=uuid, status='Running')
        with self.assertRaisesRegex(
                AppError,
                "Cannot unpause container %s in Running state" % uuid):
            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            self.app.post('/v1/containers/%s/%s/' % (test_object.uuid,
                                                     'unpause'),
                          headers=headers)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_reboot')
    def test_reboot_by_uuid(self, mock_container_reboot, mock_validate):
        test_container_obj = objects.Container(self.context,
                                               **utils.get_test_container())
        mock_container_reboot.return_value = test_container_obj
        test_container = utils.get_test_container()
        self._action_test(test_container, 'reboot', 'uuid',
                          mock_container_reboot, 202,
                          query_param='timeout=10')

    def test_reboot_by_uuid_invalid_state(self):
        uuid = uuidutils.generate_uuid()
        test_object = utils.create_test_container(context=self.context,
                                                  uuid=uuid, status='Paused')
        with self.assertRaisesRegex(
                AppError, "Cannot reboot container %s in Paused state" % uuid):
            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            self.app.post('/v1/containers/%s/%s/' % (test_object.uuid,
                                                     'reboot'),
                          headers=headers)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_reboot')
    def test_reboot_by_name_wrong_timeout_value(self, mock_container_reboot,
                                                mock_validate):
        test_container = utils.get_test_container()
        with self.assertRaisesRegex(AppError,
                                    "Invalid input for query parameters"):
            self._action_test(test_container, 'reboot', 'name',
                              mock_container_reboot, 202,
                              query_param='timeout=xyz')

    @patch('zun.compute.api.API.container_logs')
    @patch('zun.objects.Container.get_by_uuid')
    def test_get_logs_by_uuid(self, mock_get_by_uuid, mock_container_logs):
        mock_container_logs.return_value = "test"
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj

        container_uuid = test_container.get('uuid')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.get('/v1/containers/%s/logs/' % container_uuid,
                                headers=headers)

        self.assertEqual(200, response.status_int)
        mock_container_logs.assert_called_once_with(
            mock.ANY, test_container_obj, True, True, False, 'all', None)

    @patch('zun.compute.api.API.container_logs')
    @patch('zun.objects.Container.get_by_uuid')
    def test_get_logs_with_options_by_uuid(self, mock_get_by_uuid,
                                           mock_container_logs):
        mock_container_logs.return_value = "test"
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj

        container_uuid = test_container.get('uuid')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.get(
            '/v1/containers/%s/logs?stderr=True&stdout=True'
            '&timestamps=False&tail=1&since=100000000' % container_uuid,
            headers=headers)
        self.assertEqual(200, response.status_int)
        mock_container_logs.assert_called_once_with(
            mock.ANY, test_container_obj, True, True, False, '1', '100000000')

    @patch('zun.compute.api.API.container_logs')
    @patch('zun.objects.Container.get_by_uuid')
    def test_get_logs_put_fails(self, mock_get_by_uuid, mock_container_logs):
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj

        container_uuid = test_container.get('uuid')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        self.assertRaises(AppError, self.app.post,
                          '/v1/containers/%s/logs/' % container_uuid,
                          headers=headers)
        self.assertFalse(mock_container_logs.called)

    @patch('zun.compute.api.API.container_logs')
    @patch('zun.objects.Container.get_by_uuid')
    def test_get_logs_with_invalid_since(self, mock_get_by_uuid,
                                         mock_container_logs):
        invalid_sinces = ['x11', '11x', '2000-01-01 01:01:01']
        for value in invalid_sinces:
            test_container = utils.get_test_container()
            test_container_obj = objects.Container(self.context,
                                                   **test_container)
            mock_get_by_uuid.return_value = test_container_obj

            container_uuid = test_container.get('uuid')
            params = {'since': value}

            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            self.assertRaises(AppError, self.app.post,
                              '/v1/containers/%s/logs' %
                              container_uuid, params, headers=headers)
            self.assertFalse(mock_container_logs.called)

    def test_get_logs_with_invalid_state(self):
        uuid = uuidutils.generate_uuid()
        test_object = utils.create_test_container(context=self.context,
                                                  uuid=uuid, status='Creating')
        with self.assertRaisesRegex(
                AppError,
                "Cannot logs container %s in Creating state" % uuid):
            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            self.app.get('/v1/containers/%s/logs/' % test_object.uuid,
                         headers=headers)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_exec')
    @patch('zun.objects.Container.get_by_uuid')
    def test_execute_command_by_uuid(self, mock_get_by_uuid,
                                     mock_container_exec, mock_validate):
        mock_container_exec.return_value = ""
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj

        container_uuid = test_container.get('uuid')
        url = '/v1/containers/%s/%s/' % (container_uuid, 'execute')
        cmd = {'command': 'ls'}
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post(url, cmd, headers=headers)
        self.assertEqual(200, response.status_int)
        mock_container_exec.assert_called_once_with(
            mock.ANY, test_container_obj, cmd['command'], True, False)

    def test_exec_command_by_uuid_invalid_state(self):
        uuid = uuidutils.generate_uuid()
        test_object = utils.create_test_container(context=self.context,
                                                  uuid=uuid, status='Stopped')
        cmd = {'command': 'ls'}
        with self.assertRaisesRegex(
                AppError,
                "Cannot execute container %s in Stopped state" % uuid):
            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            self.app.post('/v1/containers/%s/%s/' % (test_object.uuid,
                                                     'execute'), cmd,
                          headers=headers)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_exec')
    @patch('zun.objects.Container.get_by_uuid')
    def test_execute_without_command_by_uuid(self, mock_get_by_uuid,
                                             mock_container_exec,
                                             mock_validate):
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj

        container_uuid = test_container.get('uuid')
        cmd = {'command': ''}
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        self.assertRaises(AppError, self.app.post,
                          '/v1/containers/%s/execute' %
                          container_uuid, cmd, headers=headers)
        self.assertFalse(mock_container_exec.called)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_delete')
    @patch('zun.objects.Container.get_by_uuid')
    def test_delete_container_by_uuid(self, mock_get_by_uuid,
                                      mock_container_delete, mock_validate):
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj

        container_uuid = test_container.get('uuid')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.delete('/v1/containers/%s/' % container_uuid,
                                   headers=headers)

        self.assertEqual(204, response.status_int)
        mock_container_delete.assert_called_once_with(
            mock.ANY, test_container_obj, False)
        context = mock_container_delete.call_args[0][0]
        self.assertIs(False, context.all_tenants)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_delete')
    @patch('zun.objects.Container.get_by_uuid')
    def test_delete_container_by_uuid_all_tenants(self, mock_get_by_uuid,
                                                  mock_container_delete,
                                                  mock_validate):
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj

        container_uuid = test_container.get('uuid')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.delete('/v1/containers/%s/?all_tenants=1' %
                                   container_uuid, headers=headers)

        self.assertEqual(204, response.status_int)
        mock_container_delete.assert_called_once_with(
            mock.ANY, test_container_obj, False)
        context = mock_container_delete.call_args[0][0]
        self.assertIs(True, context.all_tenants)

    def test_delete_by_uuid_invalid_state(self):
        uuid = uuidutils.generate_uuid()
        test_object = utils.create_test_container(context=self.context,
                                                  uuid=uuid, status='Running')
        with self.assertRaisesRegex(
                AppError,
                "Cannot delete container %s in Running state" % uuid):
            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            self.app.delete('/v1/containers/%s' % (test_object.uuid),
                            headers=headers)

    def test_delete_force_by_uuid_invalid_state(self):
        uuid = uuidutils.generate_uuid()
        test_object = utils.create_test_container(context=self.context,
                                                  uuid=uuid, status='Paused')
        with self.assertRaisesRegex(
                AppError,
                "Cannot delete_force container %s in Paused state" % uuid):
            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            self.app.delete('/v1/containers/%s?force=True' % test_object.uuid,
                            headers=headers)

    @patch('zun.compute.api.API.container_delete')
    def test_delete_by_uuid_invalid_state_force_true(self, mock_delete):
        uuid = uuidutils.generate_uuid()
        test_object = utils.create_test_container(context=self.context,
                                                  uuid=uuid, status='Running')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.delete('/v1/containers/%s?force=True' % (
            test_object.uuid), headers=headers)
        self.assertEqual(204, response.status_int)

    @patch('zun.compute.api.API.container_delete')
    def test_delete_by_uuid_with_force_wrong(self, mock_delete):
        uuid = uuidutils.generate_uuid()
        test_object = utils.create_test_container(context=self.context,
                                                  uuid=uuid)
        mock_delete.side_effect = exception.InvalidValue
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        self.assertRaises(AppError, self.app.delete,
                          '/v1/containers/%s?force=wrong' % test_object.uuid,
                          headers=headers)
        self.assertTrue(mock_delete.not_called)

    def test_delete_container_with_uuid_not_found(self):
        uuid = uuidutils.generate_uuid()
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        self.assertRaises(AppError, self.app.delete,
                          '/v1/containers/%s' % uuid, headers=headers)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_kill')
    @patch('zun.objects.Container.get_by_uuid')
    def test_kill_container_by_uuid(self,
                                    mock_get_by_uuid, mock_container_kill,
                                    mock_validate):
        test_container_obj = objects.Container(self.context,
                                               **utils.get_test_container())
        mock_container_kill.return_value = test_container_obj
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj

        container_uuid = test_container.get('uuid')
        url = '/v1/containers/%s/%s/' % (container_uuid, 'kill')
        cmd = {'signal': '9'}
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post(url, cmd, headers=headers)
        self.assertEqual(202, response.status_int)
        mock_container_kill.assert_called_once_with(
            mock.ANY, test_container_obj, cmd['signal'])

    def test_kill_by_uuid_invalid_state(self):
        uuid = uuidutils.generate_uuid()
        test_object = utils.create_test_container(context=self.context,
                                                  uuid=uuid, status='Stopped')
        body = {'signal': 9}
        with self.assertRaisesRegex(
                AppError, "Cannot kill container %s in Stopped state" % uuid):
            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            self.app.post('/v1/containers/%s/%s/' % (test_object.uuid,
                                                     'kill'), body,
                          headers=headers)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_kill')
    @patch('zun.objects.Container.get_by_uuid')
    def test_kill_container_which_not_exist(self,
                                            mock_get_by_uuid,
                                            mock_container_kill,
                                            mock_validate):
        mock_container_kill.return_value = ""
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj
        mock_container_kill.side_effect = Exception

        container_uuid = "edfe2a25-2901-438d-8157-fffffd68d051"
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        self.assertRaises(AppError, self.app.post,
                          '/v1/containers/%s/%s/' % (container_uuid, 'kill'),
                          headers=headers)
        self.assertTrue(mock_container_kill.called)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_kill')
    @patch('zun.objects.Container.get_by_uuid')
    def test_kill_container_with_exception(self,
                                           mock_get_by_uuid,
                                           mock_container_kill,
                                           mock_validate):
        mock_container_kill.return_value = ""
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj
        mock_container_kill.side_effect = Exception

        container_uuid = test_container.get('uuid')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        self.assertRaises(AppError, self.app.post,
                          '/v1/containers/%s/%s/' % (container_uuid, 'kill'),
                          headers=headers)
        self.assertTrue(mock_container_kill.called)

    @patch('zun.compute.api.API.container_kill')
    @patch('zun.objects.Container.get_by_uuid')
    def test_kill_container_with_invalid_singal(self,
                                                mock_get_by_uuid,
                                                mock_container_kill):
        invalid_signal = ['11x', 'x11']
        for value in invalid_signal:
            test_container = utils.get_test_container()
            test_container_obj = objects.Container(self.context,
                                                   **test_container)
            mock_get_by_uuid.return_value = test_container_obj

            container_uuid = test_container.get('uuid')
            params = {'signal': value}
            with self.assertRaisesRegex(
                    AppError, "Bad response: 400 Bad Request"):
                headers = {'OpenStack-API-Version': CURRENT_VERSION}
                self.app.post('/v1/containers/%s/kill/' %
                              container_uuid, params, headers=headers)
            self.assertFalse(mock_container_kill.called)

    @patch('zun.network.neutron.NeutronAPI.get_available_network')
    @patch('zun.compute.api.API.container_create')
    @patch('zun.compute.api.API.image_search')
    def test_create_container_resp_has_image_driver(self, mock_search,
                                                    mock_container_create,
                                                    mock_neutron_get_network):
        mock_container_create.side_effect = lambda x, y, z, v: y
        # Create a container with a command
        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512",'
                  '"environment": {"key1": "val1", "key2": "val2"},'
                  '"image_driver": "glance"}')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post('/v1/containers/',
                                 params=params, headers=headers,
                                 content_type='application/json')
        self.assertEqual(202, response.status_int)
        self.assertIn('image_driver', response.json.keys())
        self.assertEqual('glance', response.json.get('image_driver'))

    @patch('zun.compute.api.API.container_attach')
    @patch('zun.objects.Container.get_by_uuid')
    def test_attach_container_by_uuid(self, mock_get_by_uuid,
                                      mock_container_attach):
        mock_container_attach.return_value = "ws://test"
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context,
                                               **test_container)
        mock_get_by_uuid.return_value = test_container_obj

        container_uuid = test_container.get('uuid')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.get('/v1/containers/%s/attach/' % container_uuid,
                                headers=headers)

        self.assertEqual(200, response.status_int)
        mock_container_attach.assert_called_once_with(
            mock.ANY, test_container_obj)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_attach')
    @patch('zun.objects.Container.get_by_uuid')
    def test_attach_container_with_exception(self,
                                             mock_get_by_uuid,
                                             mock_container_attach,
                                             mock_validate):
        mock_container_attach.return_value = ""
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj
        mock_container_attach.side_effect = Exception

        container_uuid = test_container.get('uuid')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        self.assertRaises(AppError, self.app.get,
                          '/v1/containers/%s/attach/' % container_uuid,
                          headers=headers)
        self.assertTrue(mock_container_attach.called)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_resize')
    @patch('zun.objects.Container.get_by_name')
    def test_resize_container_by_uuid(self,
                                      mock_get_by_uuid,
                                      mock_container_resize,
                                      mock_validate):
        test_container_obj = objects.Container(self.context,
                                               **utils.get_test_container())
        mock_container_resize.return_value = test_container_obj
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj

        container_name = test_container.get('name')
        url = '/v1/containers/%s/%s/' % (container_name, 'resize')
        cmd = {'h': '100', 'w': '100'}
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post(url, cmd, headers=headers)
        self.assertEqual(200, response.status_int)
        mock_container_resize.assert_called_once_with(
            mock.ANY, test_container_obj, cmd['h'], cmd['w'])

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_resize')
    @patch('zun.objects.Container.get_by_uuid')
    def test_resize_container_with_exception(self,
                                             mock_get_by_uuid,
                                             mock_container_resize,
                                             mock_validate):
        mock_container_resize.return_value = ""
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj
        mock_container_resize.side_effect = Exception

        container_uuid = test_container.get('uuid')
        body = {'h': '100', 'w': '100'}
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        self.assertRaises(AppError, self.app.post,
                          '/v1/containers/%s/%s/' %
                          (container_uuid, 'resize'), body, headers=headers)
        self.assertTrue(mock_container_resize.called)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_top')
    @patch('zun.objects.Container.get_by_uuid')
    def test_top_command_by_uuid(self, mock_get_by_uuid,
                                 mock_container_top, mock_validate):
        mock_container_top.return_value = ""
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj

        container_uuid = test_container.get('uuid')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.get('/v1/containers/%s/top?ps_args=aux' %
                                container_uuid, headers=headers)
        self.assertEqual(200, response.status_int)
        self.assertTrue(mock_container_top.called)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_top')
    @patch('zun.objects.Container.get_by_uuid')
    def test_top_command_invalid_ps(self, mock_get_by_uuid,
                                    mock_container_top, mock_validate):
        mock_container_top.return_value = ""
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj
        mock_container_top.side_effect = Exception

        container_uuid = test_container.get('uuid')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        self.assertRaises(AppError, self.app.get,
                          '/v1/containers/%s/top?ps_args=kkkk' %
                          container_uuid, headers=headers)
        self.assertTrue(mock_container_top.called)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_get_archive')
    @patch('zun.objects.Container.get_by_uuid')
    def test_get_archive_by_uuid(self,
                                 mock_get_by_uuid,
                                 container_get_archive,
                                 mock_validate):
        container_get_archive.return_value = ("", "")
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj

        container_uuid = test_container.get('uuid')
        url = '/v1/containers/%s/%s/' % (container_uuid, 'get_archive')
        cmd = {'path': '/home/1.txt'}
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.get(url, cmd, headers=headers)
        self.assertEqual(200, response.status_int)
        container_get_archive.assert_called_once_with(
            mock.ANY, test_container_obj, cmd['path'])

    def test_get_archive_by_uuid_invalid_state(self):
        uuid = uuidutils.generate_uuid()
        test_object = utils.create_test_container(context=self.context,
                                                  uuid=uuid, status='Error')
        with self.assertRaisesRegex(
                AppError,
                "Cannot get_archive container %s in Error state" % uuid):
            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            self.app.get('/v1/containers/%s/%s/' % (test_object.uuid,
                                                    'get_archive'),
                         headers=headers)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_put_archive')
    @patch('zun.objects.Container.get_by_uuid')
    def test_put_archive_by_uuid(self,
                                 mock_get_by_uuid,
                                 container_put_archive,
                                 mock_validate):
        container_put_archive.return_value = ""
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj

        container_uuid = test_container.get('uuid')
        url = '/v1/containers/%s/%s/' % (container_uuid, 'put_archive')
        cmd = {'path': '/home/',
               'data': '/home/1.tar'}
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post(url, cmd, headers=headers)
        self.assertEqual(200, response.status_int)
        container_put_archive.assert_called_once_with(
            mock.ANY, test_container_obj, cmd['path'], cmd['data'])

    def test_put_archive_by_uuid_invalid_state(self):
        uuid = uuidutils.generate_uuid()
        test_object = utils.create_test_container(context=self.context,
                                                  uuid=uuid, status='Error')
        with self.assertRaisesRegex(
                AppError,
                "Cannot put_archive container %s in Error state" % uuid):
            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            self.app.post('/v1/containers/%s/%s/' % (test_object.uuid,
                                                     'put_archive'),
                          headers=headers)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_stats')
    @patch('zun.objects.Container.get_by_uuid')
    def test_stats_container_by_uuid(self, mock_get_by_uuid,
                                     mock_container_stats, mock_validate):
        mock_container_stats.return_value = ""
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj

        container_uuid = test_container.get('uuid')
        url = '/v1/containers/%s/stats'\
              % container_uuid
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.get(url, headers=headers)
        self.assertEqual(200, response.status_int)
        self.assertTrue(mock_container_stats.called)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_commit')
    @patch('zun.objects.Container.get_by_name')
    def test_commit_by_name(self, mock_get_by_name,
                            mock_container_commit, mock_validate):

        test_container_obj = objects.Container(self.context,
                                               **utils.get_test_container())
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_name.return_value = test_container_obj
        mock_container_commit.return_value = None
        container_name = test_container.get('name')
        url = '/v1/containers/%s/%s/' % (container_name, 'commit')
        cmd = {'repository': 'repo', 'tag': 'tag'}
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post(url, cmd, headers=headers)
        self.assertEqual(202, response.status_int)
        mock_container_commit.assert_called_once_with(
            mock.ANY, test_container_obj, cmd['repository'], cmd['tag'])

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_commit')
    @patch('zun.objects.Container.get_by_uuid')
    def test_commit_by_uuid(self, mock_get_by_uuid,
                            mock_container_commit, mock_validate):

        test_container_obj = objects.Container(self.context,
                                               **utils.get_test_container())
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_by_uuid.return_value = test_container_obj
        mock_container_commit.return_value = None
        container_uuid = test_container.get('uuid')
        url = '/v1/containers/%s/%s/' % (container_uuid, 'commit')
        cmd = {'repository': 'repo', 'tag': 'tag'}
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post(url, cmd, headers=headers)
        self.assertEqual(202, response.status_int)
        mock_container_commit.assert_called_once_with(
            mock.ANY, test_container_obj, cmd['repository'], cmd['tag'])

    def test_commit_by_uuid_invalid_state(self):
        uuid = uuidutils.generate_uuid()
        cmd = {'repository': 'repo', 'tag': 'tag'}
        utils.create_test_container(context=self.context,
                                    uuid=uuid, status='Error')
        with self.assertRaisesRegex(
                AppError, "Cannot commit container %s in Error state" % uuid):
            headers = {'OpenStack-API-Version': CURRENT_VERSION}
            self.app.post('/v1/containers/%s/commit/' % uuid, cmd,
                          headers=headers)

    @patch('zun.common.utils.validate_container_state')
    @patch('zun.compute.api.API.container_exec_resize')
    @patch('zun.api.utils.get_resource')
    def test_execute_resize_container_exec(
            self, mock_get_resource, mock_exec_resize, mock_validate):
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_resource.return_value = test_container_obj
        container_name = test_container.get('name')
        url = '/v1/containers/%s/%s/' % (container_name, 'execute_resize')
        fake_exec_id = ('7df36611fa1fc855618c2c643835d41d'
                        'ac3fe568e7688f0bae66f7bcb3cccc6c')
        kwargs = {'exec_id': fake_exec_id, 'h': '100', 'w': '100'}
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post(url, kwargs, headers=headers)
        self.assertEqual(200, response.status_int)
        mock_exec_resize.assert_called_once_with(
            mock.ANY, test_container_obj, fake_exec_id, kwargs['h'],
            kwargs['w'])

    @mock.patch('zun.common.utils.get_security_group_ids')
    @mock.patch('zun.common.utils.list_ports')
    @mock.patch('zun.api.utils.get_resource')
    def test_add_duplicate_default_security_group(self, mock_get_resource,
                                                  mock_list_ports,
                                                  mock_get_security_group_ids):
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        test_container_obj.security_groups = []
        mock_get_resource.return_value = test_container_obj
        mock_list_ports.return_value = \
            [{'security_groups': ['fake_default_security_group_id']}]
        mock_get_security_group_ids.return_value = \
            ['fake_default_security_group_id']
        container_name = test_container.get('name')
        default_security_group = 'default'
        url = '/v1/containers/%s/%s?name=%s' % (container_name,
                                                'add_security_group',
                                                default_security_group)
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post(url, headers=headers, expect_errors=True)
        self.assertEqual(400, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(
            "security_group %s already present in container" %
            default_security_group, response.json['errors'][0]['detail'])

    @mock.patch('zun.compute.api.API.add_security_group')
    @mock.patch('zun.common.utils.list_ports')
    @mock.patch('zun.api.utils.get_resource')
    def test_add_security_group_by_uuid(self, mock_get_resource,
                                        mock_list_ports,
                                        mock_add_security_group):
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_resource.return_value = test_container_obj
        mock_list_ports.return_value = \
            [{'security_groups': ['fake_default_security_group_id']}]
        container_name = test_container.get('name')
        security_group_id_to_add = '5f7cf831-9a9c-4e2b-87b2-6081667f852b'
        url = '/v1/containers/%s/%s?uuid=%s' % (container_name,
                                                'add_security_group',
                                                security_group_id_to_add)
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post(url, headers=headers)
        self.assertEqual(202, response.status_int)
        self.assertEqual('application/json', response.content_type)
        mock_add_security_group.assert_called_once_with(
            mock.ANY, test_container_obj, security_group_id_to_add)

    @mock.patch('zun.common.utils.get_security_group_ids')
    @mock.patch('zun.common.utils.list_ports')
    @mock.patch('zun.api.utils.get_resource')
    def test_add_security_group_with_invalid_uuid(self, mock_get_resource,
                                                  mock_list_ports,
                                                  mock_get_security_group_ids):
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_get_resource.return_value = test_container_obj
        mock_list_ports.return_value = \
            [{'security_groups': test_container_obj.security_groups}]
        container_name = test_container.get('name')
        invalid_uuid = 'invalid_uuid'
        url = '/v1/containers/%s/%s?uuid=%s' % (container_name,
                                                'add_security_group',
                                                invalid_uuid)
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post(url, headers=headers, expect_errors=True)
        self.assertEqual(400, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(
            "Expected a uuid but received %(uuid)s." %
            {'uuid': invalid_uuid}, response.json['errors'][0]['detail'])

    @patch('zun.network.neutron.NeutronAPI.get_neutron_network')
    @patch('zun.compute.api.API.network_detach')
    @patch('zun.objects.Container.get_by_uuid')
    def test_network_detach(self, mock_by_uuid, mock_detach, mock_get_network):
        test_container = utils.get_test_container()
        test_container_obj = objects.Container(self.context, **test_container)
        mock_by_uuid.return_value = test_container_obj
        container_uuid = test_container.get('uuid')
        mock_get_network.return_value = {'id': 'private'}
        mock_detach.return_value = None
        url = '/v1/containers/%s/%s?network=%s' % (container_uuid,
                                                   'network_detach',
                                                   'private')
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        response = self.app.post(url,
                                 headers=headers)
        self.assertEqual(202, response.status_int)
        mock_detach.assert_called_once_with(mock.ANY, test_container_obj,
                                            mock.ANY)


class TestContainerEnforcement(api_base.FunctionalTest):

    def _common_policy_check(self, rule, func, *arg, **kwarg):
        self.policy.set_rules({rule: 'project_id:non_fake'})
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        kwarg['headers'] = headers
        response = func(*arg, **kwarg)
        self.assertEqual(403, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(
            "Policy doesn't allow %s to be performed." % rule,
            response.json['errors'][0]['detail'])

    def test_policy_disallow_get_all(self):
        self._common_policy_check(
            'container:get_all', self.app.get, '/v1/containers/',
            expect_errors=True)

    def test_policy_disallow_get_all_all_tenants(self):
        self._common_policy_check(
            'container:get_all_all_tenants',
            self.app.get, '/v1/containers/?all_tenants=1',
            expect_errors=True)

    def test_policy_disallow_get_one(self):
        container = obj_utils.create_test_container(self.context)
        self._common_policy_check(
            'container:get_one', self.app.get,
            '/v1/containers/%s/' % container.uuid,
            expect_errors=True)

    def test_policy_disallow_get_one_all_tenants(self):
        container = obj_utils.create_test_container(self.context)
        self._common_policy_check(
            'container:get_one_all_tenants', self.app.get,
            '/v1/containers/%s/?all_tenants=1' % container.uuid,
            expect_errors=True)

    def test_policy_disallow_update(self):
        container = obj_utils.create_test_container(self.context)
        params = {'cpu': 1}
        self._common_policy_check(
            'container:update', self.app.patch_json,
            '/v1/containers/%s/' % container.uuid, params,
            expect_errors=True)

    def test_policy_disallow_create(self):
        params = ('{"name": "MyDocker", "image": "ubuntu",'
                  '"command": "env", "memory": "512"}')

        self._common_policy_check(
            'container:create', self.app.post, '/v1/containers/',
            params=params,
            content_type='application/json',
            expect_errors=True)

    def test_policy_disallow_delete(self):
        container = obj_utils.create_test_container(self.context)
        self._common_policy_check(
            'container:delete', self.app.delete,
            '/v1/containers/%s/' % container.uuid,
            expect_errors=True)

    def test_policy_disallow_delete_all_tenants(self):
        container = obj_utils.create_test_container(self.context)
        self._common_policy_check(
            'container:delete_all_tenants', self.app.delete,
            '/v1/containers/%s/?all_tenants=1' % container.uuid,
            expect_errors=True)

    def _owner_check(self, rule, func, *args, **kwargs):
        self.policy.set_rules({rule: "user_id:%(user_id)s"})
        headers = {'OpenStack-API-Version': CURRENT_VERSION}
        kwargs['headers'] = headers
        response = func(*args, **kwargs)
        self.assertEqual(403, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertTrue(
            "Policy doesn't allow %s to be performed." % rule,
            response.json['errors'][0]['detail'])

    def test_policy_only_owner_get_one(self):
        container = obj_utils.create_test_container(self.context,
                                                    user_id='another')
        self._owner_check("container:get_one", self.get_json,
                          '/containers/%s/' % container.uuid,
                          expect_errors=True)

    def test_policy_only_owner_update(self):
        container = obj_utils.create_test_container(self.context,
                                                    user_id='another')
        self._owner_check(
            "container:update", self.patch_json,
            '/containers/%s/' % container.uuid,
            {'cpu': 1},
            expect_errors=True)

    def test_policy_only_owner_delete(self):
        container = obj_utils.create_test_container(self.context,
                                                    user_id='another')
        self._owner_check(
            "container:delete", self.delete,
            '/containers/%s/' % container.uuid,
            expect_errors=True)

    def test_policy_only_owner_logs(self):
        container = obj_utils.create_test_container(self.context,
                                                    user_id='another')
        self._owner_check("container:logs", self.get_json,
                          '/containers/%s/logs/' % container.uuid,
                          expect_errors=True)

    def test_policy_only_owner_execute(self):
        container = obj_utils.create_test_container(self.context,
                                                    user_id='another')
        self._owner_check("container:execute", self.post_json,
                          '/containers/%s/execute/' % container.uuid,
                          params={'command': 'ls'}, expect_errors=True)

    def test_policy_only_owner_actions(self):
        actions = ['start', 'stop', 'reboot', 'pause', 'unpause']
        container = obj_utils.create_test_container(self.context,
                                                    user_id='another')
        for action in actions:
            self._owner_check('container:%s' % action, self.post_json,
                              '/containers/%s/%s/' % (container.uuid, action),
                              {}, expect_errors=True)
