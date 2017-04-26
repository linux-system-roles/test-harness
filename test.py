
import avocado
import glob
import machine
import tempfile

class Test(avocado.Test):
    def setUp(self):
        workdir = tempfile.mkdtemp(dir=self.workdir)
        if self.params.get('source', path='/run/image/*'):
            self.setUpMux(workdir)
        else:
            self.setUpLocal(workdir)

    def tearDown(self):
        if self.params.get('source', path='/run/image/*'):
            self.tearDownMux()
        else:
            self.tearDownLocal()

    def setUpMux(self, workdir):
        image = self.fetch_asset(self.params.get('source', path='/run/image/*'))
        self.machine = machine.Virtualhost(image, workdir=workdir)

        setup = self.params.get('setup', path='/run/image/*')
        if setup:
            self.machine.execute(setup)

    def tearDownMux(self):
        self.machine.terminate()

    def setUpLocal(self, workdir):
        self.machine = machine.Localhost(workdir)

    def tearDownLocal(self):
        pass

    def test(self):
        for fn in glob.glob('/role/test/test_*.yml'):
            self.machine.run_playbook(fn)
