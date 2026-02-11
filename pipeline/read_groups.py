from os.path import basename, join
import argparse
import re

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', required=True)
parser.add_argument('-p', '--patient', required=True)
args = parser.parse_args()

def get_read_groups(args):
        prefix_basename = basename(args.file)
        normal_pattern = r'.*([\-|\_]N[\-|\_])|([\-|\_]normal[\-|\_])|([\-|\_]PBMC[\-|\_]).*\.fastq\.gz|\.fq\.gz'
        tumor_pattern = r'.*([\-|\_]T[\-|\_])|([\-|\_]tumor[\-|\_]).*\.fastq\.gz|\.fq\.gz'
        if re.search(normal_pattern, prefix_basename):
                sample = "normal"
        elif re.search(tumor_pattern, prefix_basename):
                sample = "tumor"
        else:
                raise ValueError("Unexpected prefix, cannot extract SM tag: %s" % args.file)
        sample_id = "%s_%s" % (args.patient, sample)
        library = sample_id
        print("\\t".join(["@RG", "ID:%s" % args.patient, "SM:%s" % sample_id, "LB:%s" % library, "PL:Illumina"]))

#        return "\\t".join([
#                "@RG",
#                "ID:%s" % args.patient,
#                "SM:%s" % sample_id,
#                "LB:%s" % library,
#                "PL:Illumina"
#        ])


if __name__=='__main__':
    get_read_groups(args)
