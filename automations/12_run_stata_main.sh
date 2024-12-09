#!/bin/bash
set -ev

[[ "$SkipProcessing" == "yes" ]] && exit 0
[[ "$ProcessStata" == "no" ]] && exit 0

RunCommand="run.sh"

if [ -z $2 ]
then
cat << EOF
$0 (projectID) (name of main)

where (projectID) could be openICPSR, Zenodo, etc. ID. , e.g., 123456
  and (name of main) could be "main.do". 

Name should be unique, and contain no spaces. Otherwise, this will fail.

If a "$RunCommand" exists in the base of the (projectID), it will be used instead, and the 
(name of main) ignored.

EOF
exit 2
fi
projectID=$1
mainname=$2
mainsuffix=${mainname##*.}

case $mainsuffix in
   do)
   # we are fine
   ;;
   sh)
   # we execute this file instead
   RunCommand=$mainname
   ;;
   *)
   echo "Extension $mainsuffix not allowed"
   exit 2
   ;;
esac

if [ ! -d $projectID ]
then
  echo "$projectID not a directory"
  exit 2
fi

cd $projectID

# find the main program

mainloc="$(find . -name $mainname)"
maindir="$(dirname "$mainloc")"


if [[ -f $RunCommand ]]
then
  runfilex="Already exists. Using."
else
  # create runfile
  echo "#!/bin/bash" > $RunCommand 
  echo "cd \"$maindir\"" >> $RunCommand
  echo "stata-mp -b do $mainname" >> $RunCommand  
  chmod a+rx $RunCommand
  git add $RunCommand || exit 0
  runfilex="Created"
fi

printf "%40s : %20s\n" "Main name" "$mainname"
printf "%40s : %20s\n" "Directory" "$maindir"
printf "%40s : %20s\n" "Run file" "$runfilex"

# now run it.
printf "%40s : %20s\n" "Starting" "$(date +%F_%H-%m)"

bash -x "$RunCommand"
exitcode=$?
printf "%40s : %20s\n" "Exit code" "$exitcode"
printf "%40s : %20s\n" "Finished" "$(date +%F_%H-%m)"
