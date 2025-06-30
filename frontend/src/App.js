import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState('');
    const [recommendation, setRecommendation] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');


        // Fetch categories from the API when the component mounts
    useEffect(() => {
        // The API endpoint we created in Flask
        fetch('http://127.0.0.1:5000/api/categories')
            .then(response => response.json())
            .then(data => setCategories(data))
            .catch(err => console.error("Failed to fetch categories:", err));
    }, []);


    // // Fetch categories from Flask API when the component mounts
    // useEffect(() => {
    //     // The proxy will automatically send this to http://localhost:5000/api/categories
    //     // fetch('/api/categories')
    //     fetch('http://localhost:5000/api/categories', {
    //         method: 'GET',
    //         headers: { 'Content-Type': 'application/json' }
    //     })
    //     .then(response => {
    //         // First, clone the response to log its text content
    //             response.clone().text().then(text => {
    //                 console.log("Server response text:", text);
    //             });

    //             // Now, try to parse it as JSON
    //             if (!response.ok) {
    //                 throw new Error(`HTTP error! Status: ${response.status}`);
    //             }
    //             return response.json(); // This is where the error is likely happening
    //         })
    //         .then(data => {
    //             console.log("Successfully parsed JSON:", data);
    //             setCategories(data);
    //         })
    //         .catch(err => {
    //             console.error("Fetch Error:", err);
    //             setError(err.message);
    //         });
    // }, []);

    const handleGetRecommendation = () => {
        if (!selectedCategory) {
            setError('Please select a category.');
            return;
        }
        setLoading(true);
        setError('');
        setRecommendation(null);

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
                setRecommendation(data);
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
                <h1>Credit Card Recommender</h1>
                <div className="controls">
                    <select
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                    >
                        <option value="">-- Select a Category --</option>
                        {categories.map(cat => (
                            <option key={cat} value={cat}>{cat}</option>
                        ))}
                    </select>
                    <button onClick={handleGetRecommendation} disabled={loading}>
                        {loading ? 'Getting...' : 'Get Recommendation'}
                    </button>
                </div>

                {error && <p className="error-message">{error}</p>}

                {recommendation && (
                    <div className="results">
                        {recommendation.best_card && (
                            <div className="card best-card">
                                <h3>🏆 Best Option Found</h3>
                                <h4>{recommendation.best_card.name}</h4>
                                <p>Reward: {recommendation.best_card.reward_rate_for_category * 100}%</p>
                            </div>
                        )}
                         {recommendation.best_owned_card && (!recommendation.best_card || recommendation.best_card.id !== recommendation.best_owned_card.id) && (
                            <div className="card owned-card">
                                <h3>✨ Your Best Owned Card</h3>
                                <h4>{recommendation.best_owned_card.name}</h4>
                                <p>Reward: {recommendation.best_owned_card.reward_rate_for_category * 100}%</p>
                            </div>
                        )}
                    </div>
                )}
            </header>
        </div>
    );
}

export default App;