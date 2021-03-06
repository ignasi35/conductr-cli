from conductr_cli import bndl_oci
from conductr_cli.test.cli_test_case import CliTestCase, create_attributes_object, strip_margin
from io import BytesIO
import os
import shutil
import tarfile
import tempfile


class TestBndlOci(CliTestCase):
    def test_oci_image_unpack_tar_wrong_format(self):
        file = tempfile.NamedTemporaryFile()
        dest_tmpdir = tempfile.mkdtemp()

        try:
            with tarfile.open(fileobj=file, mode='w') as tar:
                tar.addfile(tarfile.TarInfo('testing'), BytesIO(b'hello'))

            file.seek(0)

            with tarfile.open(fileobj=file, mode='r') as tar:
                self.assertFalse(bndl_oci.oci_image_unpack(dest_tmpdir, tar, is_dir=False))
        finally:
            shutil.rmtree(dest_tmpdir)

    def test_oci_image_unpack_dir_wrong_format(self):
        tmpdir = tempfile.mkdtemp()
        dest_tmpdir = tempfile.mkdtemp()

        try:
            with open(os.path.join(tmpdir, 'testing'), 'wb') as file:
                file.write('hello'.encode('UTF-8'))

            self.assertFalse(bndl_oci.oci_image_unpack(dest_tmpdir, tmpdir, is_dir=True))
        finally:
            shutil.rmtree(tmpdir)
            shutil.rmtree(dest_tmpdir)

    def test_oci_image_unpack_toplevel_tar(self):
        file = tempfile.NamedTemporaryFile()
        dest_tmpdir = tempfile.mkdtemp()

        try:
            with tarfile.open(fileobj=file, mode='w') as tar:
                tar.addfile(tarfile.TarInfo('oci-layout'), BytesIO(b'hello'))

            file.seek(0)

            with tarfile.open(fileobj=file, mode='r') as tar:
                self.assertTrue(bndl_oci.oci_image_unpack(dest_tmpdir, tar, is_dir=False))

            self.assertTrue(os.path.exists(os.path.join(dest_tmpdir, 'oci-layout')))
        finally:
            shutil.rmtree(dest_tmpdir)

    def test_oci_image_unpack_nested_tar(self):
        file = tempfile.NamedTemporaryFile()
        dest_tmpdir = tempfile.mkdtemp()

        try:
            with tarfile.open(fileobj=file, mode='w') as tar:
                tar.addfile(tarfile.TarInfo('testing/nested/dirs/oci-layout'), BytesIO(b'hello'))

            file.seek(0)

            with tarfile.open(fileobj=file, mode='r') as tar:
                self.assertTrue(bndl_oci.oci_image_unpack(dest_tmpdir, tar, is_dir=False))

            self.assertTrue(os.path.exists(os.path.join(dest_tmpdir, 'oci-layout')))
        finally:
            shutil.rmtree(dest_tmpdir)

    def test_oci_image_unpack_toplevel_dir(self):
        tmpdir = tempfile.mkdtemp()
        dest_tmpdir = tempfile.mkdtemp()

        try:
            with open(os.path.join(tmpdir, 'oci-layout'), 'wb') as file:
                file.write('testing'.encode('UTF-8'))

            self.assertTrue(bndl_oci.oci_image_unpack(dest_tmpdir, tmpdir, is_dir=True))

            self.assertTrue(os.path.exists(os.path.join(dest_tmpdir, 'oci-layout')))
        finally:
            shutil.rmtree(tmpdir)
            shutil.rmtree(dest_tmpdir)

    def test_oci_image_unpack_nested_dir(self):
        tmpdir = tempfile.mkdtemp()
        dest_tmpdir = tempfile.mkdtemp()

        try:
            os.makedirs(os.path.join(tmpdir, 'testing', 'nested', 'dirs'))

            with open(os.path.join(tmpdir, 'testing', 'nested', 'dirs', 'oci-layout'), 'wb') as file:
                file.write('testing'.encode('UTF-8'))

            self.assertTrue(bndl_oci.oci_image_unpack(dest_tmpdir, tmpdir, True))

            self.assertTrue(os.path.exists(os.path.join(dest_tmpdir, 'oci-layout')))
        finally:
            shutil.rmtree(tmpdir)
            shutil.rmtree(dest_tmpdir)

    def test_oci_image_bundle_conf(self):
        base_args = create_attributes_object({
            'name': 'world',
            'component_description': 'testing desc 1',
            'tag': 'testing',
            'use_default_endpoints': True,
            'annotations': []
        })

        extended_args = create_attributes_object({
            'name': 'world',
            'component_description': 'testing desc 2',
            'version': '4',
            'compatibilityVersion': '5',
            'system': 'myapp',
            'systemVersion': '3',
            'nrOfCpus': '8',
            'memory': '65536',
            'diskSpace': '16384',
            'roles': ['web', 'backend'],
            'tag': 'latest',
            'use_default_endpoints': True,
            'annotations': []
        })

        self.assertEqual(
            bndl_oci.oci_image_bundle_conf(base_args, 'my-component', {}, {}),
            strip_margin('''|name = "world"
                            |roles = []
                            |compatibilityVersion = "0"
                            |diskSpace = 1073741824
                            |memory = 402653184
                            |nrOfCpus = 0.1
                            |version = "1"
                            |system = "world"
                            |systemVersion = "1"
                            |tags = [
                            |  "testing"
                            |]
                            |annotations {}
                            |components {
                            |  my-component {
                            |    description = "testing desc 1"
                            |    file-system-type = "oci-image"
                            |    start-command = [
                            |      "ociImageTag"
                            |      "testing"
                            |    ]
                            |    endpoints {}
                            |  }
                            |}''')
        )

        self.assertEqual(
            bndl_oci.oci_image_bundle_conf(extended_args, 'my-other-component', {}, {}),
            strip_margin('''|name = "world"
                            |version = "4"
                            |compatibilityVersion = "5"
                            |system = "myapp"
                            |systemVersion = "3"
                            |nrOfCpus = "8"
                            |memory = "65536"
                            |diskSpace = "16384"
                            |roles = [
                            |  "web"
                            |  "backend"
                            |]
                            |tags = []
                            |annotations {}
                            |components {
                            |  my-other-component {
                            |    description = "testing desc 2"
                            |    file-system-type = "oci-image"
                            |    start-command = [
                            |      "ociImageTag"
                            |      "latest"
                            |    ]
                            |    endpoints {}
                            |  }
                            |}''')
        )

    def test_oci_image_bundle_conf_endpoints(self):
        base_args = create_attributes_object({
            'name': 'world',
            'component_description': 'testing desc 1',
            'tag': 'testing',
            'use_default_endpoints': True,
            'annotations': []
        })

        config = {
            'config': {
                'ExposedPorts': {'80/udp': {}}
            }
        }

        self.assertEqual(
            bndl_oci.oci_image_bundle_conf(base_args, 'my-component', {}, config),
            strip_margin('''|name = "world"
                            |roles = []
                            |compatibilityVersion = "0"
                            |diskSpace = 1073741824
                            |memory = 402653184
                            |nrOfCpus = 0.1
                            |version = "1"
                            |system = "world"
                            |systemVersion = "1"
                            |tags = [
                            |  "testing"
                            |]
                            |annotations {}
                            |components {
                            |  my-component {
                            |    description = "testing desc 1"
                            |    file-system-type = "oci-image"
                            |    start-command = [
                            |      "ociImageTag"
                            |      "testing"
                            |    ]
                            |    endpoints {
                            |      my-component-udp-80 {
                            |        bind-protocol = "udp"
                            |        bind-port = 80
                            |        service-name = "my-component-udp-80"
                            |      }
                            |    }
                            |  }
                            |  my-component-status {
                            |    description = "Status check for oci-image component"
                            |    file-system-type = "universal"
                            |    start-command = [
                            |      "check"
                            |      "$MY_COMPONENT_UDP_80_HOST"
                            |    ]
                            |    endpoints {}
                            |  }
                            |}''')
        )

    def test_oci_image_bundle_conf_no_endpoints(self):
        base_args = create_attributes_object({
            'name': 'world',
            'component_description': 'testing desc 1',
            'tag': 'testing',
            'use_default_endpoints': False,
            'annotations': []
        })

        config = {
            'config': {
                'ExposedPorts': {'80/udp': {}}
            }
        }

        self.assertEqual(
            bndl_oci.oci_image_bundle_conf(base_args, 'my-component', {}, config),
            strip_margin('''|name = "world"
                            |roles = []
                            |compatibilityVersion = "0"
                            |diskSpace = 1073741824
                            |memory = 402653184
                            |nrOfCpus = 0.1
                            |version = "1"
                            |system = "world"
                            |systemVersion = "1"
                            |tags = [
                            |  "testing"
                            |]
                            |annotations {}
                            |components {
                            |  my-component {
                            |    description = "testing desc 1"
                            |    file-system-type = "oci-image"
                            |    start-command = [
                            |      "ociImageTag"
                            |      "testing"
                            |    ]
                            |    endpoints {}
                            |  }
                            |}''')
        )

    def test_oci_image_with_check(self):
        base_args = create_attributes_object({
            'name': 'world',
            'component_description': 'testing desc 1',
            'tag': 'testing',
            'use_default_endpoints': True,
            'annotations': {}
        })

        config = {
            'config': {
                'ExposedPorts': {'80/tcp': {}, '8080/udp': {}}
            }
        }

        self.assertEqual(
            bndl_oci.oci_image_bundle_conf(base_args, 'my-component', {}, config),
            strip_margin('''|name = "world"
                            |roles = []
                            |compatibilityVersion = "0"
                            |diskSpace = 1073741824
                            |memory = 402653184
                            |nrOfCpus = 0.1
                            |version = "1"
                            |system = "world"
                            |systemVersion = "1"
                            |tags = [
                            |  "testing"
                            |]
                            |annotations {}
                            |components {
                            |  my-component {
                            |    description = "testing desc 1"
                            |    file-system-type = "oci-image"
                            |    start-command = [
                            |      "ociImageTag"
                            |      "testing"
                            |    ]
                            |    endpoints {
                            |      my-component-tcp-80 {
                            |        bind-protocol = "tcp"
                            |        bind-port = 80
                            |        service-name = "my-component-tcp-80"
                            |      }
                            |      my-component-udp-8080 {
                            |        bind-protocol = "udp"
                            |        bind-port = 8080
                            |        service-name = "my-component-udp-8080"
                            |      }
                            |    }
                            |  }
                            |  my-component-status {
                            |    description = "Status check for oci-image component"
                            |    file-system-type = "universal"
                            |    start-command = [
                            |      "check"
                            |      "$MY_COMPONENT_TCP_80_HOST"
                            |      "$MY_COMPONENT_UDP_8080_HOST"
                            |    ]
                            |    endpoints {}
                            |  }
                            |}''')
        )

    def test_oci_image_annotations(self):
        self.maxDiff = None

        base_args = create_attributes_object({
            'name': 'world',
            'component_description': 'testing desc 1',
            'tag': 'testing',
            'use_default_endpoints': True,
            'annotations': []
        })

        config = {
            'config': {
                'ExposedPorts': {'80/tcp': {}, '8080/udp': {}}
            }
        }

        manifest = {
            'annotations': {
                'com.lightbend.test': 123,
                'description': 'hello world'
            }
        }

        self.assertEqual(
            bndl_oci.oci_image_bundle_conf(base_args, 'my-component', manifest, config),
            strip_margin('''|name = "world"
                            |roles = []
                            |compatibilityVersion = "0"
                            |diskSpace = 1073741824
                            |memory = 402653184
                            |nrOfCpus = 0.1
                            |version = "1"
                            |system = "world"
                            |systemVersion = "1"
                            |tags = [
                            |  "testing"
                            |]
                            |annotations {
                            |  com {
                            |    lightbend {
                            |      test = 123
                            |    }
                            |  }
                            |  description = "hello world"
                            |}
                            |components {
                            |  my-component {
                            |    description = "testing desc 1"
                            |    file-system-type = "oci-image"
                            |    start-command = [
                            |      "ociImageTag"
                            |      "testing"
                            |    ]
                            |    endpoints {
                            |      my-component-tcp-80 {
                            |        bind-protocol = "tcp"
                            |        bind-port = 80
                            |        service-name = "my-component-tcp-80"
                            |      }
                            |      my-component-udp-8080 {
                            |        bind-protocol = "udp"
                            |        bind-port = 8080
                            |        service-name = "my-component-udp-8080"
                            |      }
                            |    }
                            |  }
                            |  my-component-status {
                            |    description = "Status check for oci-image component"
                            |    file-system-type = "universal"
                            |    start-command = [
                            |      "check"
                            |      "$MY_COMPONENT_TCP_80_HOST"
                            |      "$MY_COMPONENT_UDP_8080_HOST"
                            |    ]
                            |    endpoints {}
                            |  }
                            |}''')
        )
