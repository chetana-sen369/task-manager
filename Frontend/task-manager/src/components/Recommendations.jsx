import React, { useState } from 'react';
const Recommendations = () => {
    const [recommendation, setRecommendation] = useState('');
    const [loading, setLoading] = useState(false);
    const fetchRecommendation = async () => {
        setLoading(true);
        try {
            const res = await fetch('http://127.0.0.1:8000/recommendations');
            const data = await res.json();
            setRecommendation(data.recommendation || 'No recommendation available.');
        }
        catch (error) {
            console.error(error);
            setRecommendation('Failed to fetch recommendation.');
        }
        finally {
            setLoading(false);
        }
    };
    return (
        <div>
            <h2>AI Recommendations</h2>
            <button onClick={fetchRecommendation} disabled={loading}>
                {loading ? 'Fetching...' : 'Get Recommendation'}
            </button> {recommendation && <p>{recommendation}</p>
            }
        </div>
    );
};
export default Recommendations;