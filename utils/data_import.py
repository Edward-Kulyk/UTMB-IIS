import pandas as pd

from app import db
from models import UTMLink


def import_excel_data(file_path):
    # Read Excel file into a pandas DataFrame
    df = pd.read_excel(file_path)

    # Iterate through DataFrame rows and add to the database
    for index, row in df.iterrows():
        utm_link = UTMLink(
            url=row["url"],
            campaign_content=row["campaign_content"],
            campaign_source=row["campaign_source"],
            campaign_medium=row["campaign_medium"],
            campaign_name=row["campaign_name"],
            domain=row["domain"],
            slug=row["slug"],
            short_id=row["short_id"],
            short_secure_url=row["short_secure_url"],
        )
        db.session.add(utm_link)

    # Commit changes to the database
    db.session.commit()
