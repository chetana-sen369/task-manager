import React from 'react';

const Recommendations = ({ recommendation, fetchRecommendations, loading }) => {
  return (
    <div>
      <h2>AI Recommendations</h2>
      <button onClick={fetchRecommendations} disabled={loading}>
        {loading ? 'Fetching...' : 'Get Recommendation'}
      </button>
      {recommendation && <p>{recommendation}</p>}
    </div>
  );
};

export default Recommendations;
