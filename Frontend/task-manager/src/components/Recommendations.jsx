import React from 'react';
import ReactMarkdown from 'react-markdown';
const Recommendations = ({ recommendation, fetchRecommendations, loading }) => {
  return (
    <div>
      <h2>AI Recommendations</h2>
      <button onClick={fetchRecommendations} disabled={loading}>
        {loading ? 'Fetching...' : 'Get Recommendation'}
      </button>
      {recommendation && (
  <div className="recommendation-box">
    {recommendation.split('\n').map((line, index) => {
  const parts = line.split(/(\*\*.*?\*\*)/g); // keep **text**

  return (
    <p key={index}>
      {parts.map((part, i) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return <strong key={i}>{part.replace(/\*\*/g, "")}</strong>;
        }
        return part;
      })}
    </p>
  );
})}
  </div>
)}
    </div>
  );
};

export default Recommendations;
