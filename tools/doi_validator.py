"""
A module to validate DOI links and convert them. 

This module sees the return of a base pattern in 10.7910/DVN/JKFYMJ format, 
as well as returning JKFYMJ. The SERVER_URL will also be returned.

Andres Aradillas Fernandez
10/15/2022
"""

# set only numbers/capital letters as valid for DOI tag
allowed_chars = set(("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"))

# Main function
def doi_validate(s):
    SERVER_URL = ""
    # checks if in "https://doi.org/10.7910/DVN/JKFYMJ" format
    if "https://doi.org/10.7910/DVN/" in s:
        # sets the SERVER_URL to Harvard
        SERVER_URL = "dataverse.harvard.edu"

        # retrieve the tag from the DOI link
        tag = s.split("https://doi.org/10.7910/DVN/", 2)[1]

        # verifies tag is in correct format
        validation = set((tag))
        if len(tag) == 6 and validation.issubset(allowed_chars):
            return tag
        else:
            return "invalid format"
    # checks if in "https://dataverse.harvard.edu/..." format
    elif "https://" in s and "/dataset.xhtml?persistentId=doi:10.7910/DVN/" in s:
        # retrieve the SERVER_URL
        temp = s.split("https://", 1)[1]
        SERVER_URL = temp.split("/dataset.xhtml?persistentId=doi:10.7910/DVN/", 1)[0]

        # retrieve the tag from the DOI link
        tag = temp.split("/dataset.xhtml?persistentId=doi:10.7910/DVN/", 1)[1]

        # verifies tag is in correct format
        validation = set((tag))
        if len(tag) == 6 and validation.issubset(allowed_chars):
            return tag
        else:
            return "invalid format"
    # check if in "10.7910/DVN/JKFYMJ" format
    elif "10.7910/DVN/" in s:
        tag = s.split("10.7910/DVN/", 1)[1]

        # verifies tag is in correct format
        validation = set((tag))
        if len(tag) == 6 and validation.issubset(allowed_chars):
            return tag
        else:
            return "invalid format"
    else:
        return "invalid format"

