import os
import pandas as pd
from govinfo import GovInfo


class DirStats:

    @staticmethod
    def count_pdf_files(directory):
        pdf_count = 0
        if not os.path.exists(directory):
            raise FileNotFoundError(f"The directory {directory} does not exist.")
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path) and item.endswith('.pdf'):
                pdf_count += 1
        return pdf_count

    @staticmethod
    def count_xml_files(directory):
        xml_count = 0
        if not os.path.exists(directory):
            raise FileNotFoundError(f"The directory {directory} does not exist.")
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path) and item.endswith('.xml'):
                xml_count += 1
        return xml_count

    @staticmethod
    def get_file_stats(df, dir=""):
        """Get stats for XML or PDF files in directories specified in the DataFrame."""
        current_directory = os.getcwd() + "/" + dir
        folder_data = []

        for index, row in df.iterrows():
            folder_path = os.path.join(current_directory, row['collectioncode'])
            if os.path.isdir(folder_path):  # Check if it's a folder
                if dir == "xml":
                    file_count = DirStats.count_xml_files(folder_path)
                elif dir == "pdf":
                    file_count = DirStats.count_pdf_files(folder_path)
                else:
                    file_count = 0

                folder_data.append({"folder_name": row['collectioncode'], f"count_{dir}": file_count})

        file_stats_df = pd.DataFrame(folder_data)

        df = df.merge(file_stats_df, left_on="collectioncode", right_on="folder_name", how="left")
        df[f"count_{dir}"] = df[f"count_{dir}"].fillna(0).astype(int)

        # Calculate percentage completion and status
        df[f"completion_percentage_{dir}"] = df.apply(
            lambda row: (row[f"count_{dir}"] / row['packagecount']) * 100 if row['packagecount'] > 0 else 0, axis=1
        )
        
        # If you want to display the status based on percentage:
        df[f"status_{dir}"] = df.apply(
            lambda row: f"{row[f'completion_percentage_{dir}']:.2f}%" if row['packagecount'] > 0 else 'No Data', axis=1
        )

        df.drop('folder_name', axis=1, inplace=True)
        return df


#df = GovInfo.gpo_collections(api_key="ARqzwi0cCCjsdpdoeVv2Iv4I0FbhTVoSo7urYs1e")
#df = df.sort_values(by='packagecount').reset_index(drop=True)

#df = DirStats.get_file_stats(df, "xml")
#df = DirStats.get_file_stats(df, "pdf")

#df.drop('completion_percentage_xml', axis=1, inplace=True)
#df.drop('completion_percentage_pdf', axis=1, inplace=True)

#print(df)
