import React, { useState } from 'react';
import axios from 'axios';
import FinetuneForm from './components/FinetuneForm';
import JobStatus from './components/JobStatus';
import './App.css';

const API_URL = "http://localhost:8000/api/v1";

function App() {
    const [job, setJob] = useState(null);
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleJobSubmit = async (formData) => {
        setIsLoading(true);
        setError('');
        setJob(null);
        try {
            const response = await axios.post(`${API_URL}/jobs`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setJob(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || "An unexpected error occurred.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="App">
            <h1>On-Demand Model Finetuning</h1>
            <FinetuneForm onSubmit={handleJobSubmit} isLoading={isLoading} />
            {error && <div className="status-box"><p className="status-message error">Error: {error}</p></div>}
            {job && <JobStatus initialJob={job} apiUrl={API_URL} />}
        </div>
    );
}

export default App;