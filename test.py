import unittest
import shutil
import tempfile
import json
from uuid import uuid4
from os.path import dirname, join, splitext
from glob import glob

from openaddr import cache, conform, jobs

class TestCache (unittest.TestCase):
    
    def setUp(self):
        ''' Prepare a clean temporary directory, and copy sources there.
        '''
        jobs.setup_logger(False)
        
        self.testdir = tempfile.mkdtemp(prefix='test-')
        self.src_dir = join(self.testdir, 'sources')
        sources_dir = join(dirname(__file__), 'tests', 'sources')
        shutil.copytree(sources_dir, self.src_dir)
        
        # Rename sources with random characters so S3 keys are unique.
        uuid = uuid4().hex
        
        for path in glob(join(self.src_dir, '*.json')):
            base, ext = splitext(path)
            shutil.move(path, '{0}-{1}{2}'.format(base, uuid, ext))
    
    def tearDown(self):
        shutil.rmtree(self.testdir)
    
    def test_parallel(self):
        sources = glob(join(self.src_dir, '*.json'))
        caches = jobs.run_all_caches(sources, 'openaddresses-tests')
        conformed = jobs.run_all_conforms(sources, 'openaddresses-tests')
    
        for (source, cache) in caches.items():
            # OpenAddresses-Cache will add three keys to the source file.
            self.assertTrue('cache' in cache)
            self.assertTrue('version' in cache)
            self.assertTrue('fingerprint' in cache)
    
        for (source, conform) in conformed.items():
            # OpenAddresses-Conform will add a processed key to the
            # source file, if the conform data was present initially.
            if 'san_francisco' in source or 'alameda_county' in source:
                self.assertTrue(type(conform) is str)
            else:
                self.assertTrue(conform is None)

    def test_serial(self):
        source = glob(join(self.src_dir, '*.json'))[0]
        cache(source, self.testdir, 'openaddresses-tests')
    
        with open(source) as file:
            data = json.load(file)
            
            # OpenAddresses-Cache will add three keys to the source file.
            self.assertTrue('cache' in data)
            self.assertTrue('version' in data)
            self.assertTrue('fingerprint' in data)
            print data['cache']
            print data['version']
            print data['fingerprint']

        print ''
        
        conform(source, self.testdir, 'openaddresses-tests')
    
        with open(source) as file:
            data = json.load(file)
            
            # OpenAddresses-Conform will add a processed key to the
            # source file, if the conform data was present initially.
            if 'conform' in data:
                self.assertTrue('processed' in data)
            else:
                self.assertFalse('processed' in data)
            print data.get('processed', None)

if __name__ == '__main__':
    unittest.main()
