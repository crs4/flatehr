#!/usr/bin/env bash

source $(dirname $0)/argparse.bash || exit 1
argparse "$@" <<EOF || exit 1
parser.add_argument('infile')
parser.add_argument('-s', '--server', type=str, help='openehr base url', default='http://localhost:8089')
parser.add_argument('-l', '--login', type=str, help='user:password', default='ehrbase-user:SuperSecretPassword')
parser.add_argument('-t', '--template', type=str, help='web template', required=True)
parser.add_argument('-c', '--conf', type=str, help='composition generation conf', required=True)
parser.add_argument('-p', '--processes', type=int, help='Parallel processes used', default=1)
parser.add_argument('-n', '--namespace', type=str, help='namespace for ehr creation', required=True)
EOF
# set -xeuo

echoerr() { printf "%s\n" "$*" >&2; }

template_id=$(cat $TEMPLATE | jq -r .templateId)

mkdir -p compositions
ls $INFILE  | xargs -n1 -P $PROCESSES   flatehr generate from-file -c $CONF -t $TEMPLATE | \
  tqdm --total $(ls $INFILE | wc -l)  | \
  while read ext_id  comp ; do    
    # echoerr $ext_id
    ehr_payload="{ \"_type\": \"EHR_STATUS\", \"archetype_node_id\": \"openEHR-EHR-EHR_STATUS.generic.v1\", \"name\": { \"value\": \"EHR Status\" }, \"subject\": { \"external_ref\": { \"id\": { \"_type\": \"GENERIC_ID\", \"value\": \"$ext_id\", \"scheme\": \"id_scheme\" }, \"namespace\": \"$NAMESPACE\", \"type\": \"PERSON\" } }, \"is_modifiable\": true, \"is_queryable\": true }"
    ehr_id=$(curl -s -X POST -d "$ehr_payload"  -u ehrbase-user:SuperSecretPassword -H 'Prefer: return=representation' -H 'Content-type: application/json '  $SERVER/ehrbase/rest/openehr/v1/ehr  | jq -r .ehr_id.value)
    echo $comp > compositions/${ehr_id}.json
    # set -xeuo
    curl -s -X POST  -u $LOGIN -H 'Content-type: application/json' "$SERVER/ehrbase/rest/ecis/v1/composition/?format=FLAT&ehrId=$ehr_id&templateId=$template_id"  -d "$comp" &>>  out  ;


  done

