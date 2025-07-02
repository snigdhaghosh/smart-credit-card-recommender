import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Card from './components/card'; // Import the new Card component
import './App.css';

function App() {
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState('');
    const [recommendation, setRecommendation] = useState({ best_card: null, other_options: [] });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');


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
            <p>Select a category to find the best credit card for your needs.</p>
        </header>

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
    </div>
    );
}

export default App;
