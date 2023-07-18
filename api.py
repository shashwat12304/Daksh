from flask import Flask, request
from flask_restful import Api, Resource
import pickle
from sklearn.preprocessing import StandardScaler

# instantiate Flask Rest Api
app = Flask(__name__)
api = Api(app)

# load the pickled model and X_train
X_train = pickle.load(open('X_train.sav', 'rb'))
model = pickle.load(open('model.sav', 'rb'))

# feature scale data after fitting scalar object to pickled training set
sc = StandardScaler()
X_train = sc.fit_transform(X_train)

# Create class for Api Resource
class Records(Resource):
    def get(self):
        # get request that returns the JSON format for API request
        return {
            "JSON data format": {
                "Url": "https://example.com"
            }
        }, 200

    def post(self):
        # post request
        # make model and X_train global variables
        global model
        global X_train
        # it gets patient's record and returns the ML model's prediction
        data = request.get_json()

        try:
            url = data["Url"]

            # Convert URL into a tuple
            url_tuple = (
                0,  # id
                url.count("."),  # NumDots
                url.count(".") - 1,  # SubdomainLevel
                url.count("/") - 2,  # PathLevel
                len(url),  # UrlLength
                url.count("-"),  # NumDash
                url.split("/")[2].count("-"),  # NumDashInHostname
                1 if "@" in url else 0,  # AtSymbol
                1 if "~" in url else 0,  # TildeSymbol
                url.count("_"),  # NumUnderscore
                url.count("%"),  # NumPercent
                url.count("?"),  # NumQueryComponents
                url.count("&"),  # NumAmpersand
                url.count("#"),  # NumHash
                sum(c.isdigit() for c in url),  # NumNumericChars
                1 if url.startswith("https://") else 0,  # NoHttps
                1 if len(url.split("/")[-1]) > 30 else 0,  # RandomString
                1 if any(c.isdigit() for c in url.split("/")[2]) else 0,  # IpAddress
                1 if url.split("/")[2].count(".") > 1 else 0,  # DomainInSubdomains
                1 if url.count("/") > 3 else 0,  # DomainInPaths
                1 if "https" in url.split("/")[2] else 0,  # HttpsInHostname
                len(url.split("/")[2]),  # HostnameLength
                len(url.split("/")[-1]),  # PathLength
                len(url.split("?")[-1]),  # QueryLength
                1 if "//" in url else 0,  # DoubleSlashInPath
                0,  # NumSensitiveWords (not specified in the URL)
                0,  # EmbeddedBrandName (not specified in the URL)
                0,  # PctExtHyperlinks (not specified in the URL)
                0,  # PctExtResourceUrls (not specified in the URL)
                0,  # ExtFavicon (not specified in the URL)
                0,  # InsecureForms (not specified in the URL)
                0,  # RelativeFormAction (not specified in the URL)
                0,  # ExtFormAction (not specified in the URL)
                0,  # AbnormalFormAction (not specified in the URL)
                0,  # PctNullSelfRedirectHyperlinks (not specified in the URL)
                0,  # FrequentDomainNameMismatch (not specified in the URL)
                0,  # FakeLinkInStatusBar (not specified in the URL)
                0,  # RightClickDisabled (not specified in the URL)
                0,  # PopUpWindow (not specified in the URL)
                0,  # SubmitInfoToEmail (not specified in the URL)
                0,  # IframeOrFrame (not specified in the URL)
                0,  # MissingTitle (not specified in the URL)
                0,  # ImagesOnlyInForm (not specified in the URL)
                0,  # SubdomainLevelRT (not specified in the URL)
                0,  # UrlLengthRT (not specified in the URL)
                0,  # PctExtResourceUrlsRT (not specified in the URL)
                0,  # AbnormalExtFormActionR (not specified in the URL)
                0,  # ExtMetaScriptLinkRT (not specified in the URL)
                0   # PctExtNullSelfRedirectHyperlinksRT (not specified in the URL)
            )

            # feature scale the data
            scaled_data = sc.transform([url_tuple])
            # dictionary containing the diagnosis with the key as the model's prediction
            diagnosis = {
                0: 'Your Result is Normal',
                1: 'Diabetes Detected'
            }
            # pass scaled data to model for prediction
            new_pred = model.predict(scaled_data)[0]
            # get corresponding value from the diagnosis dictionary (using the model prediction as the key)
            result = diagnosis.get(new_pred)
            return {'Diagnosis': result}, 200
        except:
            # if client sends the wrong request or data type then return correct format
            return {
                'Error! Please use this JSON format': {
                    "Url": "https://example.com"
                }
            }, 500


# Add the URI of the Records resource
api.add_resource(Records, '/')

# Run the API
if __name__ == '__main__':
    app.run(port=5000, debug=True)
