import json
import requests
import pandas as pd
from typing import Union
from typing import Optional

BASE_URL='https://api.govinfo.gov/'
header_key = {'X-Api-key': 'ARqzwi0cCCjsdpdoeVv2Iv4I0FbhTVoSo7urYs1e'} # PPP
#header_key = {'X-Api-key': '0y40jiRIp8yg6cnZXVKI9cZqo1izWnExmDjNIKdm'} # CPD
class GovInfo:

    def gpo_collections(
        collection: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page_size: int = 100,
        doc_class: Optional[str] = None,
        congress: Optional[int] = None,
        bill_version: Optional[str] = None,
        court_code: Optional[str] = None,
        court_type: Optional[str] = None,
        state: Optional[str] = None,
        topic: Optional[str] = None,
        is_glp: Optional[str] = None,
        nature_suit_code: Optional[str] = None,
        nature_suit: Optional[str] = None,
        offset_mark: str = "*",
    ) -> Union[pd.DataFrame, None]:
        """
        Retrieve GPO collections data.

        Parameters are similar to the original R function.

        Returns:
            A pandas DataFrame containing the requested data, or None if no data is found.
        """
        # Base URL for the API
        base_url = "https://api.govinfo.gov"

        # Setting up the query parameters
        params = {
            "pageSize": page_size,
            "docClass": doc_class,
            "congress": congress,
            "billVersion": bill_version,
            "courtCode": court_code,
            "courtType": court_type,
            "state": state,
            "topic": topic,
            "isGLP": is_glp,
            "natureSuitCode": nature_suit_code,
            "natureSuit": nature_suit,
            "offsetMark": offset_mark
        }

        # Constructing the request URL
        url = f"{base_url}/collections"
        if collection:
            url += f"/{collection}"
        if start_date:
            url += f"/{start_date}"
        if end_date:
            url += f"/{end_date}"
            
        # Making the API request
        headers = {"X-Api-Key": header_key['X-Api-key']} if header_key['X-Api-key'] else {}
        response = requests.get(url, headers=headers, params={k: v for k, v in params.items() if v is not None})
        response.raise_for_status()
        body = response.json()

        # Handling paginated data
        if "nextPage" in body:
            first_page = pd.DataFrame(body.get("packages", []))
            next_page_url = body["nextPage"]
            all_data = [first_page]

            while next_page_url:
                next_response = requests.get(next_page_url, headers=headers)
                next_response.raise_for_status()
                next_body = next_response.json()
                all_data.append(pd.DataFrame(next_body.get("packages", [])))
                next_page_url = next_body.get("nextPage")

            df = pd.concat(all_data, ignore_index=True)
        else:
            if collection:
                df = pd.DataFrame(body.get("packages", []))
            else:
                df = pd.DataFrame(body.get("collections", []))

        # Cleaning and formatting the DataFrame
        if not df.empty:
            df.columns = df.columns.str.lower()
            if "last_modified" in df.columns:
                df["last_modified"] = pd.to_datetime(df["last_modified"])
            if "congress" in df.columns:
                df["congress"] = pd.to_numeric(df["congress"], errors="coerce").astype("Int64")
            if "date_issued" in df.columns:
                df["date_issued"] = pd.to_datetime(df["date_issued"]).dt.date

        return df if not df.empty else None

    def package_data(package_id):
        '''request JSON summary of the package and return list of download options'''
        response = requests.get(
            BASE_URL+'packages/'+package_id+'/summary',
            headers = header_key
            )
        summary=json.loads(response.text)
        #print(f"Title: {summary['title']}")
        #print(f"This package was originally published on {summary['dateIssued']}")
        #if summary['relatedLink']:
        #    print(f"There are relationships available at {summary['relatedLink']}")
        #    print()
        #print('Available download types:')
        #for link_type in summary['download']:
        #    print(link_type,summary['download'][link_type])
        #file_type= "pdfLink"#input("Which file type do you want? ")
        #link = summary['download'][file_type]
        return summary # link

    def package_data_verbose(package_id):
        '''request JSON summary of the package and return list of download options'''
        response = requests.get(
            BASE_URL+'packages/'+package_id+'/summary',
            headers = header_key
            )
        summary=json.loads(response.text)
        print(f"Title: {summary['title']}")
        print(f"This package was originally published on {summary['dateIssued']}")
        if summary['relatedLink']:
            print(f"There are relationships available at {summary['relatedLink']}")
            print()
        print('Available download types:')
        for link_type in summary['download']:
            print(link_type,summary['download'][link_type])
        print()
        #file_type= "pdfLink"#input("Which file type do you want? ")
        #link = summary['download'][file_type]
        return summary # link

    def get_file(file_link):
        """Fetch the requested file type from the given link."""
        response = requests.get(
            file_link,
            headers=header_key
        )
        response.raise_for_status()  # Raise an error if the request fails
        return response
