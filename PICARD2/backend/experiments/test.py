# - Log in
# - Check experiment history. Empty
# - Check datasets. Empty + public
# - Check scripts. Empty + public
# - Add dataset D.
# - Check datasets. D + public
# - Add script P (py).
# - Add script J (jar).
# - Check scripts. P + J + public
# - Create experiment D + P = E.
# - Check experiments.  E running
# - Watch E for passphrase.
# - Check until E is complete.
# - Get E results: Check against expected
# - Check experiments. E not running.
# - Check datasets. D + public
# - Check scripts. S + public
# - Delete D.
# - Delete S.
# - Check datasets. Empty + public
# - Check scripts. Empty + public
# - Log out.
# - Check datasets. Not allowed
# - Check scripts. Not allowed
# - Check experiments. Not allowed
import requests



# 1. Set your local or production endpoint
url = "http://localhost:5000"

# 2. Define the data you want to send
login_data = {
    "username": "testuser",
    "password": "testpassword123"
}
def test_login(data):
    # 3. Send the POST request using the 'json' parameter
    # This automatically sets Content-Type to 'application/json'
    response = requests.post(url + "/user_login/", json=data)

    # 4. Check the results
    if response.status_code == 200:
        print("Success:", response.json())
    else:
        print(f"Failed login (Status {response.status_code}):")
        print(response)

def test_signup(data):
    response = requests.post(url, json=data)

    response = requests.post(url + "/signup/", json=data)

    if response.status_code == 200:
        print("Success:", response.json())
    else:
        print(f"Failed signup (Status {response.status_code}):")
        print(response)

test_login(login_data)
test_signup(login_data)
test_login(login_data)

print("Yippeee")
