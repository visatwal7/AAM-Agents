#!/bin/bash

domains=("Cor_configurable_services" "NPL_tool" "precertification")

pip install -r Tools/CVSH_ODM/tools/requirements.txt

echo Importing elv connections
for file in connections/*.yaml; do
  echo Importing $file
  orchestrate connections import -f "${file}"  
done

echo Setting odm connection creds
odm_username=$(yq '.odm.credentials.USERNAME' dev-config.yaml)
odm_password=$(yq '.odm.credentials.PASSWORD' dev-config.yaml)

echo "odm_base_url:"

orchestrate connections set-credentials -a odm --env draft -e USERNAME="${odm_username}" -e PASSWORD="${odm_password}"

echo Importing tools
for domain in "${domains[@]}" ; do
  echo Importing $domain tools
  orchestrate tools import -k python -r Tools/CVSH_ODM/tools/requirements.txt -a odm -p ./Tools -f "Tools/CVSH_ODM/tools/${domain}/${domain}_tool.py"   
done

echo Importing agents
for domain in "${domains[@]}" ; do
    echo Importing $domain agent
    orchestrate agents import -f Agents/${domain}_agent.yaml
done

