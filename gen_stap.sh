#!/bin/bash

kernel_release="$(uname -r)"

function usage() {
  echo $1
  echo "Usage:"
  echo " -e, --entry func, must options here, you could use module.func style if this function name is ambiguity"
  echo " -m, --modules modules, put multi modules splitted with comma(,)"
  echo " -k, --kernel_funcs , put multi kernel funcs splitted with comma(,), e.g. *@block/*"
  echo " -f, --force_cache"
  echo " -o, --out_stap"
  echo " -r, --release, use the specified kernel release, in case more than one is available on your machine"
  echo " -v, --verbose, probe suffix ?"
  echo " e.g. ./gen_stap.sh -m iscsi_target_mod.ko,target_core_mod.ko,target_core_file.ko,target_core_pscsi.ko -e fd_do_rw"
  echo "e.g. ./gen_stap.sh -m iscsi_target_mod.ko,target_core_mod.ko,target_core_file.ko,target_core_pscsi.ko -e iscsi_target_mod.rx_data"
  echo "e.g. ./gen_stap.sh -m sg,scsi_transport_spi,libata,mptspi,vmw_pvscsi,sd_mod,sr_mod,mptscsih,scsi_mod,scsi_debug -k \"*@block/*, *@kernel/*\" -e scsi_request_fn"
}
function make_caches() {
  cache_dir=~/.kernel_visualization.cache/${kernel_release}
  modules_cache_file=$cache_dir/modules_list
  kfunc_cache_file=$cache_dir/kfunc_list
  mfunc_cache_file=$cache_dir/mfunc_list

  if [[ ( $force_cache -eq 1 ) || ( ! -d $cache_dir ) ]];then
    mkdir $cache_dir
    echo "Caching modules list"
    find /lib/modules/${kernel_release}/ -type f -name "*.ko" > $modules_cache_file

    echo "Caching kernel funciton list"
    cat /boot/System.map-${kernel_release} | grep -v ' U ' | awk '{print $3}' >$kfunc_cache_file

    echo "Caching modules funciton list"
    cat $modules_cache_file | while read m;do name=`basename $m .ko`;nm --defined-only $m | awk -v name=$name '{print name, $3}';done >$mfunc_cache_file
  fi
}

verbose=0
force_cache=0
cmd="$0 $@"
while [[ $# > 1 ]]
do
  key="$1"

  case $key in
    -e|--entry)
      entry="$2"
      shift # past argument
      ;;
    -m|--modules)
      modules="$2"
      shift # past argument
      ;;
    -k|--kfuncs)
      kfuncs="$2"
      shift # past argument
      ;;
    -o|--out)
      out_stap="$2"
      shift # past argument
      ;;
    -r|--release)
      kernel_release="$2"
      shift # past argument
      ;;
    -v|--verbose)
      verbose=1
      ;;
    -f|--force_cache)
      force_cache=1
      ;;
    *)
      usage
      exit
      ;;
  esac
  shift # past argument or value
done


[[ -z $entry ]] && usage && exit
[[ -z $out_stap ]] && out_stap=$entry.stap

if [[ ! -d "/lib/modules/${kernel_release}" ]]; then
  echo "[-] Unable to find kernel modules for release ${kernel_release}"
  usage
  exit 1
fi

if [[ ! -f "/boot/System.map-${kernel_release}" ]]; then
  echo "[-] Unable to find system map for ${kernel_release}"
  usage
  exit 1
fi

calls=""
returns=""

make_caches

###########################################################
# Parse entry func, it could like iscsi_target_mod.rx_data
###########################################################
probe=$entry
found_probe=0
IFS=. read cur_m cur_f <<<$entry
[[ -z $cur_f ]] && cur_f=$entry && cur_m=""

if [[ -n `cat $kfunc_cache_file | grep -w $cur_f` ]];then
  found_probe=1;probe='kernel.function("'$cur_f'")'
elif [[ -n `cat $mfunc_cache_file | grep -w $cur_f` ]];then
  found_probe=1;
  entry_module=`cat $mfunc_cache_file | grep -w $cur_f | awk '{print $1}'`
  if [[ `cat $mfunc_cache_file | grep -w $cur_f | wc -l` -gt 1 ]];then
    [[ -z $cur_m ]] && echo -e "[-] These modules have this function definition: \n$entry_module" && exit
    probe=`printf "module(\"%s\").function(\"%s\")" $cur_m $cur_f`
    entry_module=$cur_m
  else
    probe=`cat $mfunc_cache_file | grep -w $cur_f | awk '{printf "module(\"%s\").function(\"%s\")", $1, $2}'`
  fi
  [[ -z `echo  $modules | grep -w $entry_module` ]] && modules="$modules,$entry_module"
fi
[[ $found_probe -eq 0 ]] && usage "[-] Couldn't find $entry" && exit

###########################################################
# Parse modules func
###########################################################
[[ -n $modules ]] && for i in ${modules//,/ }
do
  # find modules first
  if [ -z "`cat $modules_cache_file | grep -w $i`" ];then continue;fi
  i=`basename $i .ko`
  i="module(\"$i\").function(\"*\")"
  if [[ -n $calls ]];then # non empty
    calls="$calls,\n  ""$i.call"
    returns="$returns,\n  ""$i.return"
  else
    calls="probe $i.call"
    returns="probe $i.return"
  fi
  [[ $verbose -eq 0 ]] && calls="$calls""?" && returns="$returns""?"
done

###########################################################
# Parse kernel func
###########################################################
[[ -n $kfuncs ]] && for i in ${kfuncs//,/ }
do
  i="kernel.function(\"$i\")"
  if [[ -n $calls ]];then # non empty
    calls="$calls,\n  ""$i.call"
    returns="$returns,\n  ""$i.return"
  else
    calls="probe $i.call"
    returns="probe $i.return"
  fi
  [[ $verbose -eq 0 ]] && calls="$calls""?" && returns="$returns""?"
done

if [ -z "$calls" ];then
  calls="probe kernel.function(\"*\").call?"
  returns="probe kernel.function(\"*\").return?"
fi

echo "[+] Entry func: $probe"
echo "[+] Inject modules: $modules"
echo "[+] Inject kernel funcs: $kfuncs"
echo "[+] Out_stap: $out_stap"
echo "[+] Force cache: $force_cache"
echo "[+] Probe check: $verbose"


sed -e "s:\$1:$probe:g" -e "s:probe \$2.call:$calls:g" -e "s:probe \$2.return:$returns:g" stap_base.stp >$out_stap
cat >>$out_stap <<EOF
##############################################################################
#                      Generated by gen_stap.sh using cmd:
#                          $cmd
#                      Author: Feng Li (lifeng1519@gmail.com)
EOF
chmod a+x $out_stap
cat $out_stap
