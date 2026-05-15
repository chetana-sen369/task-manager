import React, { useState } from 'react';

const GenerateTaskForm = ({ fetchTasks }) => {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error,setError]=useState('');
  const handleGenerate = async () => {
    if (!prompt) return;
    setLoading(true);
    setError('');//clear any previous errors
    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/generate_task`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Couldn't generate task . Please try again later! ");
      }
      //clear the error when the request is successfull 
      setError('');
      const newTask = await res.json(); // this is the new task object
      setPrompt('');
      fetchTasks(newTask); // trigger a refresh in TaskList
    } catch (error) {
      console.error(error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Generate Task via AI</h2>
      <input
        type="text"
        placeholder="Enter a task prompt..."
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      />
      <button onClick={handleGenerate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Task'}
      </button>
      {error && (
        <div style={{ color: 'red', marginTop: '10px', fontSize: '14px' }}>
          {error}
        </div>
      )}
    </div>
  );
};

export default GenerateTaskForm;
