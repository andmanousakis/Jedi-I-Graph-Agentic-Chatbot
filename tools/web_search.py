import os
import httpx

class SearchWeb:

    def __init__(self):

        # Initialize the web search tool with a query.
        self.api_key = os.getenv("SERPER_API_KEY")
    
    def pipeline(self, query: str) -> tuple[str, str]:

        # Perform a web search using the Serper API.
        url = "https://google.serper.dev/search"

        # Set up headers and data for the request.
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

        # Prepare the data payload with the search query.
        data = {
            "q": query
        }

        try:

            # Make the POST request to the Serper API.
            response = httpx.post(url, headers=headers, json=data)

            # Check if the response was successful.
            response.raise_for_status()

            # Parse the JSON response.
            result = response.json()

            # Extract the top organic result snippet and link.
            if "organic" in result and result["organic"]:

                # Get the first organic result.
                top = result["organic"][0]

                # Return the snippet and link, or default messages if not found.
                return top.get("snippet", "No snippet found."), top.get("link", "No link found.")
            
            # If no organic results are found, return a default message.
            else:

                # Log that no results were found.
                return "No result found.", "N/A"
            
        except Exception as e:

            # Log any errors that occur during the search.
            return f"Error during search: {e}", "N/A"
    
    @classmethod
    def run(cls, query: str) -> tuple[str, str]:
        
        # Create an instance of the SearchWeb class.
        instance = cls()

        # Call the pipeline method with the provided query.
        return instance.pipeline(query)