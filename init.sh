#get current directory
DIR=$(pwd)

FIREBASE_CONFIG=$DIR/firebase_service_account.json
export GOOGLE_APPLICATION_CREDENTIALS="$FIREBASE_CONFIG"

echo "$GOOGLE_APPLICATION_CREDENTIALS"

