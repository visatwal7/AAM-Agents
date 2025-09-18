# contact_us_tool.py (GetContactUsInfoRule)
import json
import base64
import requests
from typing import Optional, Dict, Any, List

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from ibm_watsonx_orchestrate.agent_builder.connections import ConnectionType, ExpectedCredentials
from ibm_watsonx_orchestrate.run import connections


@tool(
    permission=ToolPermission.READ_ONLY,
    expected_credentials=[
        ExpectedCredentials(app_id="odm", type=ConnectionType.KEY_VALUE)
    ],
    description="Calls ODM GetContactUsInfoRule API to retrieve contact information for Aetna health plans based on plan details like carrier, product, coverage type, contract, and PBP."
)
def get_sample_info(
    # ---- Mandatory parameters (from your curl body) ----
    carrierOrg: str,
    product: List[str],
    coverageType: str,
    contract: str,
    pbp: str,
    lobCd: str,
    transactionID: str,
    asOfDate: str,
    
    # ---- Optional parameters ----
    supplementalProducts: Optional[str] = None,
    vBIDReq: Optional[str] = None,
    nextGenPlanSponsorId: Optional[str] = None,
    externalPlanID: Optional[str] = None,
    contractState: Optional[str] = None,
    idSource: Optional[str] = None,
    decision_id: Optional[str] = None,
) -> str:
    """
    Calls ODM GetContactUsInfoRule API to retrieve contact information for Aetna health plans.

    Mandatory: carrierOrg, product, coverageType, contract, pbp, lobCd, transactionID, asOfDate
    Optional: supplementalProducts, vBIDReq, nextGenPlanSponsorId, externalPlanID, 
              contractState, idSource, decision_id

    Returns:
        str: JSON-serialized response from the ODM service.
    """
    # ---- KV config ----
    cfg = connections.key_value("odm")
    url = cfg.get(
        "CONTACT_US_URL",
        cfg.get(
            "URL",
            "https://cpd-cp4ba-starter.apps.itz-sxxzab.infra01-lb.dal14.techzone.ibm.com/odm/DecisionService/rest/GetContactUsInfoRuleApp/3.0/V2GetContactUsInfoRule/1.0",
        ),
    )
    username = cfg.get("USERNAME")
    password = cfg.get("PASSWORD")
    cookie = cfg.get("COOKIE")  # optional

    # ---- Validate creds ----
    missing_cfg = [k for k, v in dict(USERNAME=username, PASSWORD=password).items() if not v]
    if missing_cfg:
        raise ValueError(
            f"Missing ODM credentials in KV 'odm': {', '.join(missing_cfg)}. "
            "Expected keys: USERNAME, PASSWORD (optionally CONTACT_US_URL/URL, COOKIE)."
        )

    # ---- Validate mandatory inputs ----
    mandatory_inputs = {
        "carrierOrg": carrierOrg,
        "product": product,
        "coverageType": coverageType,
        "contract": contract,
        "pbp": pbp,
        "lobCd": lobCd,
        "transactionID": transactionID,
        "asOfDate": asOfDate
    }
    
    missing_inputs = [
        k for k, v in mandatory_inputs.items() 
        if (v is None or (isinstance(v, str) and not v.strip()) or (isinstance(v, list) and not v))
    ]
    
    if missing_inputs:
        raise ValueError(f"Missing mandatory inputs: {', '.join(missing_inputs)}")

    # ---- Auth headers ----
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Basic {token}",
    }
    if cookie:
        headers["Cookie"] = cookie

    # ---- Payload (matching your curl structure exactly) ----
    payload: Dict[str, Any] = {
        "contactUsRequest": {
            "supplementalProducts": supplementalProducts or "string",
            "transactionID": transactionID,
            "asOfDate": asOfDate,
            "carrierOrg": carrierOrg,
            "product": product,
            "coverageType": coverageType,
            "contract": contract,
            "pbp": pbp,
            "vBIDReq": vBIDReq or "string",
            "lobCd": lobCd,
            "nextGenPlanSponsorId": nextGenPlanSponsorId or "string",
            "externalPlanID": externalPlanID or "string",
            "contractState": contractState or "string",
            "idSource": idSource or "string"
        }
    }
    
    if decision_id:
        payload["__DecisionID__"] = decision_id

    # ---- Call service ----
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    return json.dumps(resp.json())