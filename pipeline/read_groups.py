from os.path import basename, join
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', required=True)
parser.add_argument('-p', '--patient', required=True)
args = parser.parse_args()

def get_read_groups(args):
        prefix_basename = basename(args.file)
        if "normal" in prefix_basename or "_N_" in prefix_basename or "_PBMC_" in prefix_basename:
                sample = "normal"
        elif "tumor" in prefix_basename or "_T_" in prefix_basename:
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
