import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Card from './components/card'; // Import the new Card component
import './App.css';
import Login from './components/Login';
import Register from './components/Register';

function App() {
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState('');
    const [recommendation, setRecommendation] = useState({ best_card: null, other_options: [] });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [currentUser, setCurrentUser] = useState(null);
    const [authView, setAuthView] = useState('login');

    // // Check login status when the app loads
    // useEffect(() => {
    //     fetch('http://127.0.0.1:5000/api/status')
    //         .then(res => res.json())
    //         .then(data => {
    //             if (data.logged_in) {
    //                 setCurrentUser(data.user);
    //             }
    //         });
    // }, []);

    // Checks if the user is already logged in when the app first loads.
    useEffect(() => {
        fetch('http://127.0.0.1:5000/api/status', { credentials: 'include' })
            .then(res => res.json())
            .then(data => {
                if (data.logged_in) {
                    setCurrentUser(data.user);
                }
            })
            .catch(err => console.error("API status check failed:", err));
    }, []);

    // Fetches categories only when the user is logged in.
    useEffect(() => {
        if (currentUser) {
            fetch('http://127.0.0.1:5000/api/categories', { credentials: 'include' })
                .then(response => response.json())
                .then(data => setCategories(data))
                .catch(err => console.error("Failed to fetch categories:", err));
        }
    }, [currentUser]); // This effect re-runs when currentUser changes.

    // This function now lives in App.js and will be passed to the Login component.
    const handleLogin = async (email, password) => {
        const response = await fetch('http://127.0.0.1:5000/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
            credentials: 'include',
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to log in');
        }

        // On successful login, update the state. This triggers the UI change.
        setCurrentUser(data.user);
    };

    // // Handle user logout
    // const handleLogout = () => {
    //     fetch('/api/logout', { method: 'POST' })
    //         .then(() => {
    //             setCurrentUser(null);
    //             window.location.reload();
    //         });
    // };

    const handleLogout = () => {
        fetch('http://127.0.0.1:5000/api/logout', { 
            method: 'POST',
            credentials: 'include'
        })
        .then(() => {
            setCurrentUser(null);
            setCategories([]); // Clear categories on logout
        });
    };

    // to handle the registration API call.
    const handleRegister = async (username, email, password) => {
        const response = await fetch('http://127.0.0.1:5000/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password }),
            credentials: 'include',
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Failed to register');
        }
        // After successful registration, switch to the login view.
        setAuthView('login');
    };


    useEffect(() => {
        // The API endpoint we created in Flask
        fetch('http://127.0.0.1:5000/api/categories')
            .then(response => response.json())
            .then(data => setCategories(data))
            .catch(err => console.error("Failed to fetch categories:", err));
    }, []);



    const handleGetRecommendation = () => {
        if (!selectedCategory) {
            setError('Please select a category.');
            return;
        }
        setLoading(true);
        setError('');
        setRecommendation({ best_card: null, other_options: [] });

        // Call our new recommend API endpoint
        fetch('http://127.0.0.1:5000/api/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ category: selectedCategory }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                setError(data.error);
            } else {
                // The backend sends 'best_card' and 'eligible_cards'
                setRecommendation({
                    best_card: data.best_card,
                    other_options: data.eligible_cards || []
                });
            }
        })
        .catch(err => {
            setError('Failed to fetch recommendation. Is the backend server running?');
        })
        .finally(() => {
            setLoading(false);
        });
    };

    return (
        <div className="App">
            <header className="App-header">
                <h1>Smart Credit Card Recommender</h1>
                <div className="auth-section">
                    {currentUser ? (
                        <div>
                            <span>Welcome, {currentUser.email}</span>
                            <button onClick={handleLogout} className="logout-button">Logout</button>
                        </div>
                    ) : (
                        <span></span>
                    )}
                </div>
            </header>
            
            {!currentUser ? (
                // If the user is not logged in, show either Login or Register.
                authView === 'login' ? (
                    <Login 
                        onLogin={handleLogin} 
                        toggleView={() => setAuthView('register')} 
                    />
                ) : (
                    <Register 
                        onRegister={handleRegister} 
                        toggleView={() => setAuthView('login')} 
                    />
                )
            ) : (
                // If the user is logged in, show the recommender app content.
            <>
            <div className="controls-container">
                <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                >
                    <option value="">-- Select a Category --</option>
                    {categories.map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                    ))}
                </select>
                <button onClick={handleGetRecommendation} className="recommend-button" disabled={loading}>
                    {loading ? 'Finding...' : 'Find My Card'}
                </button>
            </div>

            {error && <p className="error-message">{error}</p>}

            <div className="recommendations-container">
                {recommendation.best_card && (
                    <div className="best-option-section">
                        <h2>Your Top Recommendation</h2>
                        <Card card={recommendation.best_card} isBestOption={true} />
                    </div>
                )}
                {recommendation.other_options && recommendation.other_options.length > 0 && (
                    <div className="other-options-section">
                        <h3>Other Great Cards to Consider</h3>
                        <div className="cards-grid">
                            {recommendation.other_options.map(card => (
                            <Card key={card.id} card={card} isBestOption={false} />
                            ))}
                        </div>
                    </div>
                )}
            </div>
            </>
            )}
        </div>
    );
}

export default App;
