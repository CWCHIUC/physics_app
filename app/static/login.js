// Import the functions you need from the SDKs
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.1/firebase-app.js";
import { getAuth, signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/10.13.1/firebase-auth.js";

// Your Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyAePKoRpI5glE6vP5sGQMvaAHuZNmoBwhY",
    authDomain: "physicsapp-e6f45.firebaseapp.com",
    projectId: "physicsapp-e6f45",
    storageBucket: "physicsapp-e6f45.appspot.com",
    messagingSenderId: "163786593137",
    appId: "1:163786593137:web:e6c9e873686fdc90db1cd0"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Add event listener for the form submission
document.getElementById('login-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the form from submitting and redirecting

    // Get input values
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    // Validate that inputs are not empty
    if (!email || !password) {
        // alert('Please fill in both email and password.');
        return;
    }

    // Try to sign in with Firebase Authentication
    signInWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            // Signed in successfully
            const user = userCredential.user;
            // alert('Login successful!');
            window.location.href = '/home'; // Redirect to home page
        })
        .catch((error) => {
            // Handle errors here.
            const errorCode = error.code;
            const errorMessage = error.message;

            // Show a more user-friendly error message
            if (errorCode === 'auth/user-not-found') {
                alert('User not found. Please check your email.');
            } else if (errorCode === 'auth/wrong-password') {
                alert('Incorrect password. Please try again.');
            } else if (errorCode === 'auth/invalid-email') {
                alert('Invalid email format.');
            } else {
                alert(errorMessage); // Default error message for other cases
            }
        });
});
