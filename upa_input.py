#!/usr/bin/python

#####################################
#####        HPG Lab            #####
#####    updated Oct  2018      #####
#####       MJJ                 #####
#####################################

# Author: Matthew Jobin, UCSC Human Paleogenomics Lab
import shutil
import os
import upa_util
from Bio import bgzf


##
def stripchr(flist, verbose, cmdfile, logfile):
    """ Strips 'chr' from BAM files

    :param flist: File list.
    :param verbose: Verbose output to log.
    :param cmdfile: File storing external commands invoked.
    :param logfile: Output log.
    :return:
    """
    print "\nStripping chr from chromosome names..."
    for i in range(len(flist)):
        sample = flist[i]
        stripchrcmd = "samtools view -H " + sample + ".bam | sed -e 's/SN:chr1/SN:1/' | sed -e 's/SN:chr2/SN:2/' | sed -e 's/SN:chr3/SN:3/' | sed -e 's/SN:chr4/SN:4/' | sed -e 's/SN:chr5/SN:5/' | sed -e 's/SN:chr6/SN:6/' | sed -e 's/SN:chr7/SN:7/' | sed -e 's/SN:chr8/SN:8/' | sed -e 's/SN:chr9/SN:9/' | sed -e 's/SN:chr10/SN:10/' | sed -e 's/SN:chr11/SN:11/' | sed -e 's/SN:chr12/SN:12/' | sed -e 's/SN:chr13/SN:13/' | sed -e 's/SN:chr14/SN:14/' | sed -e 's/SN:chr15/SN:15/' | sed -e 's/SN:chr16/SN:16/' | sed -e 's/SN:chr17/SN:17/' | sed -e 's/SN:chr18/SN:18/' | sed -e 's/SN:chr19/SN:19/' | sed -e 's/SN:chr20/SN:20/' | sed -e 's/SN:chr21/SN:21/' | sed -e 's/SN:chr22/SN:22/' | sed -e 's/SN:chrX/SN:X/' | sed -e 's/SN:chrY/SN:Y/' | sed -e 's/SN:chrM/SN:MT/' | samtools reheader - " + sample + ".bam > " + sample + ".intermediate.bam"
        upa_util.bash_command(stripchrcmd, verbose, cmdfile, logfile)
        shutil.move(sample + ".bam", sample + ".wchr.bam")
        shutil.move(sample + ".intermediate.bam", sample + ".bam")




def addreadgroup(flist, binloc, verbose, cmdfile, logfile):
    """ Adds the read group information by using Picard

    :param flist: File list.
    :param verbose: Verbose output to log.
    :param cmdfile: File storing external commands invoked.
    :param logfile: Output log.
    :return:
    """
    for i in range(len(flist)):
        sample = flist[i]
        basename = upa_util.name_strip(sample)
        addrgcmd = "java -jar " + binloc + "picard.jar AddOrReplaceReadGroups I=" + sample + ".bam O=" + sample + ".intermediate.bam RGID=4 RGLB=" + sample + " RGPL=illumina RGPU=BerkeleyHiSeq RGSM=" + basename + " VALIDATION_STRINGENCY=LENIENT"
        upa_util.bash_command(addrgcmd, verbose, cmdfile, logfile)
        shutil.move(sample + ".bam", sample + ".norg.bam")
        shutil.move(sample + ".intermediate.bam", sample + ".bam")


def bcfmpileup(flist, ref, bcname, regionrestrict, diploid, q, threads, cmdfile, logfile):
    """ Call genotypes using BCFTools.

    :param flist: File list.
    :param ref: Reference genome.
    :param bcname: Base name of input file.
    :param verbose: Verbose output to log.
    :param cmdfile: File storing external commands invoked.
    :param logfile: Output log.
    :return: Name of merged sample VCF.
    """
    print "\nCreating mpileup consensus using BCFTools and writing as a VCF..."
    mpileupcmd = "bcftools mpileup --threads " + threads + " -C 50 -d 8000 -Ov -f " + ref + " -q " + q + " "
    for i in range(len(flist)):
        sample = flist[i]
        mpileupcmd = mpileupcmd + sample + ".bam" + " "
    if regionrestrict:
        mpileupcmd = mpileupcmd + " -r " + regionrestrict
    mpileupcmd = mpileupcmd + " | bcftools call --threads " + threads + " -Oz -m -o " + bcname + "-samples.vcf.gz - "
    if diploid:
        pass
    else:
        mpileupcmd = mpileupcmd + " --ploidy 1 "
    upa_util.bash_command(mpileupcmd, False, cmdfile, logfile)
    return bcname + "-samples.vcf.gz"


def genocaller(flist, bedfile, bcname, indent, ref, regionrestrict, threads, verbose, cmdfile, logfile):
    """ Calls genotypes using Krishna Veeramah's GenoCaller_indent

    :param flist: File list.
    :param bedfile: UCSC-style BED file.
    :param bcname: Base name of input file.
    :param indent: Indent depth to each end of read.
    :param ref: Reference genome.
    :param regionrestrict: Area of genome to limit calling.
    :param threads: Number of multiprocessing threads to use.
    :param verbose: Verbose output to log.
    :param cmdfile: File storing external commands invoked.
    :param logfile: Output log.
    :return: Name of merged sample VCF.
    """
    print "\nGenoCaller..."
    samplevcfnames = []
    for i in range(len(flist)):
        sample = flist[i]
        gccmd = "GenoCaller_indent.py " + sample + ".bam " + bedfile + " " + ref + " " + indent
        upa_util.bash_command(gccmd, verbose, cmdfile, logfile)

        #Must compress to allow bcftools to merge

        with open(sample + "." + bedfile + ".indent" + str(indent) + ".vcf", 'r') as f_in, bgzf.open(sample + "." + bedfile + ".indent" + str(indent) + ".vcf.gz", 'wb') as f_out:
        # with open(sample + "." + bedfile + ".indent" + str(indent) + ".vcf", 'r') as f_in, gzip.open(sample + "." + bedfile + ".indent" + str(indent) + ".vcf.gz", 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

        samplevcfname = sample + "." + bedfile + ".indent" + str(indent) + ".vcf.gz"
        # sampleemitallname = sample + "." + bedfile + ".indent" + str(indent) + ".emit_all.vcf.gz"

        if os.path.isfile(samplevcfname):
            upa_util.vcf_name_strip(samplevcfname)
            upa_util.bash_command("bcftools index --threads " + threads + " " + samplevcfname, verbose, cmdfile, logfile)
            samplevcfnames.append(samplevcfname)
        else:
            print "ERROR: Cannot find " + samplevcfname

    #Merge the resulting VCFs together using bcftools
    bcfmergecmd = "bcftools merge --threads " + threads + " -Oz -o " + bcname + "-samples.vcf.gz "
    if regionrestrict:
        bcfmergecmd = bcfmergecmd + " -r " + regionrestrict
    for samplevcfname in samplevcfnames:
        bcfmergecmd = bcfmergecmd + samplevcfname + " "
    upa_util.bash_command(bcfmergecmd, verbose, cmdfile,logfile)
    return bcname + "-samples.vcf"

