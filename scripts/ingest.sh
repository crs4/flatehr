#!/usr/bin/env bash

source $(dirname $0)/argparse.bash || exit 1
argparse "$@" <<EOF || exit 1
parser.add_argument('infile')
parser.add_argument('-s', '--server', type=str, help='openehr base url', default='http://localhost:8089')
parser.add_argument('-l', '--login', type=str, help='user:password', default='ehrbase-user:SuperSecretPassword')
parser.add_argument('-t', '--template', type=str, help='web template', required=True)
parser.add_argument('-c', '--conf', type=str, help='composition generation conf', required=True)
parser.add_argument('-p', '--processes', type=int, help='Parallel processes used', default=1)
EOF
# set -xeu
template_id=$(cat $TEMPLATE | jq -r .templateId)
ls $INFILE  | xargs -n1 -P $PROCESSES   flatehr generate from-file -c $CONF -t $TEMPLATE | \
  tqdm --total $(ls $INFILE | wc -l)  | \
  while read ehr_id  comp ; do curl -X POST  -u $LOGIN -H 'Content-type: application/json' "$SERVER/ehrbase/rest/ecis/v1/composition/?format=FLAT&ehrId=92edfe4a-89ed-41ae-8485-de96f928664b&templateId=$template_id"  -d "$comp" ; done

