# Copyright (c) 2018. Mount Sinai School of Medicine
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import glob
from os import chdir, listdir
from os.path import dirname, join
from shutil import copy2
import tempfile
import unittest

import snakemake
import yaml

from run_snakemake import main as docker_entrypoint, \
    default_vaxrank_targets, somatic_vcf_targets

class TestPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workdir = tempfile.TemporaryDirectory()
        cls.referencedir = tempfile.TemporaryDirectory()
        cls.inputdir = tempfile.TemporaryDirectory()
        cls.config_tmpfile = tempfile.NamedTemporaryFile(mode='w', delete=True)
        cls.dna_only_config_tmpfile = tempfile.NamedTemporaryFile(mode='w', delete=True)
        cls.populate_config('idh1_config.yaml', cls.config_tmpfile)
        cls.populate_config('idh1_config_dna_only.yaml', cls.dna_only_config_tmpfile)
        cls.populate_test_files()

    @classmethod
    def tearDownClass(cls):
        cls.referencedir.cleanup()
        cls.workdir.cleanup()
        cls.inputdir.cleanup()
        cls.config_tmpfile.close()

    @classmethod
    def populate_test_files(cls):
        # populate reference files with placeholder content
        files_to_populate = [
            'b37decoy.fasta', 'b37decoy.dict', 'b37decoy.fasta.contigs', 'b37decoy.fasta.done',
            'transcripts.gtf', 'dbsnp.vcf', 'cosmic.vcf', 'S04380110_Covered_grch37_with_M.bed'
        ]
        for path in files_to_populate:
            with open(join(cls.referencedir.name, path), 'w') as f:
                f.write('placeholder')

        for path in glob.glob('datagen/*.fastq.gz'):
            copy2(path, cls.inputdir.name)

    @classmethod
    def populate_config(cls, basename, dest_tempfile):
        with open(join(cls._get_test_dir_path(), basename), 'r') as idh1_config_file:
            config_file_contents = idh1_config_file.read()
        # kinda gross, but: replace /outputs, /reference-genome, /inputs paths in config file with
        # temp dir locations
        config_file_contents = config_file_contents.replace(
            '/outputs', cls.workdir.name).replace(
            '/reference-genome/b37decoy', cls.referencedir.name).replace(
            '/inputs', cls.inputdir.name)
        dest_tempfile.write(config_file_contents)
        dest_tempfile.seek(0)

    @classmethod
    def _get_test_dir_path(cls):
        return dirname(__file__)

    @classmethod
    def _get_pipeline_dir_path(cls):
        return join(cls._get_test_dir_path(), '..', 'pipeline')

    def test_vaxrank_targets(self):
        with open(join(self._get_test_dir_path(), 'idh1_config.yaml'), 'r') as idh1_config_file:
            config = yaml.load(idh1_config_file)
        targets = default_vaxrank_targets(config)
        expected_targets = (
            '/outputs/idh1-test-sample/vaccine-peptide-report_netmhcpan-iedb_mutect-strelka.txt',
            '/outputs/idh1-test-sample/vaccine-peptide-report_netmhcpan-iedb_mutect-strelka.json',
            '/outputs/idh1-test-sample/vaccine-peptide-report_netmhcpan-iedb_mutect-strelka.pdf',
            '/outputs/idh1-test-sample/vaccine-peptide-report_netmhcpan-iedb_mutect-strelka.xlsx',
        )
        self.assertEqual(len(expected_targets), len(targets))
        for target in targets:
            self.assertTrue(target in expected_targets)

    def test_somatic_vcf_targets(self):
        with open(join(self._get_test_dir_path(), 'idh1_config.yaml'), 'r') as idh1_config_file:
            config = yaml.load(idh1_config_file)
        targets = somatic_vcf_targets(config)
        expected_targets = (
            '/outputs/idh1-test-sample/mutect.vcf',
            '/outputs/idh1-test-sample/strelka.vcf',
        )
        self.assertEqual(len(expected_targets), len(targets))
        for target in targets:
            self.assertTrue(target in expected_targets)

    # This simulates a dry run on the test data, and mostly checks rule graph validity.
    def test_workflow_compiles(self):
        chdir(self._get_pipeline_dir_path())
        self.assertTrue(snakemake.snakemake(
            'Snakefile',
            cores=20,
            resources={'mem_mb': 160000},
            configfile=self.config_tmpfile.name,
            config={'num_threads': 22, 'mem_gb': 160, 'contigs': ['2']},
            dryrun=True,
            printshellcmds=True,
            targets=[
                join(
                    self.workdir.name, 
                    'idh1-test-sample',
                    'vaccine-peptide-report_netmhcpan-iedb_mutect-strelka.txt'),
                join(
                    self.workdir.name,
                    'idh1-test-sample',
                    'rna_final.bam'),
                ],
            stats=join(self.workdir.name, 'idh1-test-sample', 'stats.json')
        ))

    def test_dna_only_setup(self):
        cli_args = [
            '--configfile', self.dna_only_config_tmpfile.name,
            '--dry-run',
            '--memory', '15',
            '--somatic-variant-calling-only',
        ]
        # run to make sure it doesn't crash
        docker_entrypoint(cli_args)

    def test_docker_entrypoint_script(self):
        cli_args = [
            '--configfile', self.config_tmpfile.name,
            '--dry-run',
            '--memory', '32',
            '--target', join(
                self.workdir.name,
                'idh1-test-sample',
                'rna_final.bam'),  # valid target
        ]
        # run to make sure it doesn't crash
        docker_entrypoint(cli_args)

        ok_dna_target_cli_args = [
            '--configfile', self.config_tmpfile.name,
            '--dry-run',
            '--memory', '15',
            '--target', join(
                self.workdir.name, 
                'idh1-test-sample',
                'mutect.vcf'),
        ]
        docker_entrypoint(ok_dna_target_cli_args)

        variant_target_cli_args = [
            '--configfile', self.config_tmpfile.name,
            '--dry-run',
            '--somatic-variant-calling-only',
            '--memory', '15',
        ]
        docker_entrypoint(variant_target_cli_args)

        germline_variant_cli_args = [
            '--configfile', self.config_tmpfile.name,
            '--dry-run',
            '--memory', '15',
            '--target', join(
                self.workdir.name, 
                'idh1-test-sample',
                'filtered_covered_normal_germline_snps_indels.vcf'),
        ]
        docker_entrypoint(germline_variant_cli_args)

    def test_docker_entrypoint_script_reference_target(self):
        reference_cli_args = [
            '--configfile', self.config_tmpfile.name,
            '--dry-run',
            '--memory', '33',
            '--target', join(
                self.referencedir.name,
                'b37decoy.dict'),
        ]
        docker_entrypoint(reference_cli_args)

    def test_docker_entrypoint_script_fastqc(self):
        qc_cli_args = [
            '--configfile', self.config_tmpfile.name,
            '--dry-run',
            '--memory', '33',
            '--target', join(
                self.workdir.name,
                'idh1-test-sample',
                'fastqc.done'),
        ]
        docker_entrypoint(qc_cli_args)

    def test_docker_entrypoint_script_picard(self):
        qc_cli_args = [
            '--configfile', self.config_tmpfile.name,
            '--dry-run',
            '--memory', '33',
            '--target', join(
                self.workdir.name,
                'idh1-test-sample',
                'normal_aligned_coordinate_sorted_dups_indelreal_bqsr_hs_metrics.txt'),
        ]
        docker_entrypoint(qc_cli_args)

    def test_docker_entrypoint_script_failures(self):
        # check that invalid targets fail
        fake_target_cli_args = [
            '--configfile', self.config_tmpfile.name,
            '--dry-run',
            '--memory', '32',
            '--target', join(
                self.workdir.name, 
                'idh1-test-sample',
                'fakey_fakerson'),
        ]
        self.assertRaises(ValueError, docker_entrypoint, fake_target_cli_args)

        bad_vaxrank_target_cli_args = [
            '--configfile', self.config_tmpfile.name,
            '--dry-run',
            '--memory', '32',
            '--target', join(
                self.workdir.name, 
                'idh1-test-sample',
                'vaccine-peptide-report_netmhcpan-iedb_mutect-strelka-mutect2.txt'),
        ]
        self.assertRaises(ValueError, docker_entrypoint, bad_vaxrank_target_cli_args)

        bad_rna_target_cli_args = [
            '--configfile', self.config_tmpfile.name,
            '--dry-run',
            '--memory', '15',
            '--target', join(
                self.workdir.name, 
                'idh1-test-sample',
                'rna_final.bam'),
        ]
        self.assertRaises(ValueError, docker_entrypoint, bad_rna_target_cli_args)
