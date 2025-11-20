#!/usr/bin/env bash

API_URL="http://127.0.0.1:8000/triage"

print() { 
  echo -e "\n---- $1 ----"
  curl -s -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "$2" | jq .
}

print "Checkout error" \
'{"description": "Checkout keeps failing with error 500 on mobile."}'

print "Login issue" \
'{"description": "I cannot login even though the password is correct."}'

print "Billing double charge" \
'{"description": "I have been charged twice for the same order, please refund."}'

print "Slow performance" \
'{"description": "Dashboard is loading extremely slow today."}'

print "How-To question" \
'{"description": "How do I invite team members to my workspace?"}'

print "New-Issue" \
'{"description": "The app switches from dark mode to light mode randomly after a few minutes."}'

print "New-Issue" \
'{
  "description": "The application unexpectedly switches from dark mode to light mode after a few minutes of use. This behavior appears to happen at random intervals and does not require any interaction from the user. The issue occurs even when dark mode has been explicitly selected in the settings. It affects usability at night or in low-light environments, causing sudden screen brightness changes that may strain the eyes. The problem persists across multiple sessions, and restarting the app does not prevent it from happening again."
}'

echo -e "\n---- Test Complete ----"
