#!bin/bash
echo "There is $# input"
echo -n "They are:"

for i in "$@";do
	echo -n "$i " # elminate the \n at last
done
echo ""
