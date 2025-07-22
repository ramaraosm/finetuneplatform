import React, { useState, useEffect, useRef } from 'react'; // Import useRef
import axios from 'axios';

// InferencePage Component - Moved to be defined BEFORE App Component
const InferencePage = ({ base_model, job_id, huggingface_repo, onBack }) => {
  const [prompt, setPrompt] = useState('');
  const [generatedText, setGeneratedText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    setIsLoading(true);
    setError('');
    setGeneratedText('');

    try {
      // API call to your Python backend
      //const response = await axios.get(`${apiUrl}/jobs/${currentJobId}`);
      //const updatedJob = response.data;
      const inferApiUrl = "http://localhost:8000/api/v1/inference/generate_text"; // Replace with your backend URL

      const response = await fetch(inferApiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          base_model: base_model,
          job_id: job_id,  
          prompt: prompt,
          huggingface_repo: huggingface_repo, // Pass the Hugging Face model ID to the backend
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Backend API error: ${response.status} - ${errorData.error || 'Unknown error'}`);
      }

      const result = await response.json();
      if (result.result) {
        setGeneratedText(result);
      } else {
        setError("No text generated or unexpected response structure from backend.");
      }
    } catch (err) {
      console.error("Error during generation:", err);
      setError(`Failed to generate text: ${err.message}. Ensure your Python backend is running.`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="inference-container p-6 bg-white rounded-2xl shadow-xl border border-gray-200">
      <button
        onClick={onBack}
        className="back-button mb-6 flex items-center text-blue-600 hover:text-blue-800 font-semibold transition duration-150 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-75 rounded-lg p-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
        Back to Main
      </button>

      <h2 className="text-3xl font-extrabold text-gray-800 mb-4 text-center">
        Model Inference
      </h2>
      
      <div className="input-section mb-6">
        <label htmlFor="prompt-input" className="block text-lg font-medium text-gray-700 mb-2">
          Enter your prompt:
        </label>
        <textarea
          id="prompt-input"
          className="w-full p-4 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 transition duration-150 ease-in-out resize-y text-gray-800"
          rows="6"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g., Describe a futuristic city powered by renewable energy."
        ></textarea>
        <br></br>
        <button
          className="mt-5 w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-4 rounded-lg shadow-md transition duration-200 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-opacity-75"
          onClick={handleGenerate}
          disabled={isLoading || !prompt.trim()}
        >
          {isLoading ? (
            <div className="flex items-center justify-center">
              <svg className="animate-spin h-5 w-5 text-white mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Generating...
            </div>
          ) : (
            'Generate Text'
          )}
        </button>
      </div>

      {error && (
        <div className="error-message mt-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg shadow-sm">
          <p className="font-bold mb-2">Error:</p>
          <p>{error}</p>
        </div>
      )}

      {generatedText && (
        <div className="generated-output mt-6 p-5 bg-blue-50 border border-blue-200 rounded-lg shadow-inner">
          <h3 className="text-xl font-semibold text-blue-800 mb-3">Generated Output:</h3>
          <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">{generatedText}</p>
        </div>
      )}
    </div>
  );
};

const JobStatus = ({ initialJob, apiUrl }) => {
    const [job, setJob] = useState(initialJob);
    const intervalRef = useRef(null); // Create a ref to store the interval ID
    const [showInferencePage, setShowInferencePage] = useState(false);

    useEffect(() => {
        // Immediately set the job when initialJob changes (e.g., a new job is submitted)
        setJob(initialJob);

        // Clear any existing interval when initialJob changes
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
        }

        const pollStatus = async (currentJobId) => {
            try {
                const response = await axios.get(`${apiUrl}/jobs/${currentJobId}`);
                const updatedJob = response.data;
                setJob(updatedJob);

                // If the job is no longer QUEUED or RUNNING, clear the interval
                if (updatedJob.status !== 'QUEUED' && updatedJob.status !== 'RUNNING') {
                    if (intervalRef.current) {
                        clearInterval(intervalRef.current);
                    }
                }
            } catch (error) {
                console.error("Failed to fetch job status:", error);
                // In case of an error, you might want to stop polling as well
                if (intervalRef.current) {
                    clearInterval(intervalRef.current);
                }
            }
        };

        // Start polling if the initial job status is QUEUED or RUNNING
        if (initialJob.status === 'QUEUED' || initialJob.status === 'RUNNING') {
            // Immediately poll once
            pollStatus(initialJob.id);

            // Set up the interval for subsequent polls
            intervalRef.current = setInterval(() => {
                // Pass the current job ID to pollStatus
                pollStatus(job.id); // It's safer to use a ref or ensure the ID is always current if not in dependencies
                                    // However, initialJob.id is stable here.
            }, 5000); // Poll every 5 seconds
        }

        // Cleanup function to clear the interval when the component unmounts
        // or when initialJob changes and a new interval is set up
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [initialJob, apiUrl]); // Dependencies: only re-run effect when initialJob or apiUrl changes


    const getStatusClassName = () => {
        switch (job.status) {
            case 'COMPLETED': return 'success';
            case 'FAILED': return 'error';
            case 'RUNNING': return 'running';
            default: return '';
        }
    };

    return (
       <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4 font-sans">
       <div className="bg-white p-8 rounded-2xl shadow-xl max-w-2xl w-full border border-gray-200">
        {!showInferencePage ? (
        <div className="status-box">
            <h3>Job Status</h3>
            <p><strong>Job ID:</strong> {job.id}</p>
            <p><strong>Model Name:</strong> {job.new_model_name}</p>
            <p>
                <strong>Status:</strong>{' '}
                <span className={`status-message ${getStatusClassName()}`}>{job.status}</span>
            </p>
            {job.status === 'COMPLETED' && (
                <p className="status-message success">
                    Success! Your model is available at:{' '}
                    <a href={`https://huggingface.co/${process.env.REACT_APP_HUGGING_FACE_USERNAME}/Finetuned-${job.new_model_name}`} target="_blank" rel="noopener noreferrer">
                        Hugging Face Hub
                    </a>
                    <br></br>
                    <button
                        className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition duration-200 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-opacity-75"
                        onClick={() => setShowInferencePage(true)}
                        >
                        Go to Inference Page
                    </button>
                </p>
            )}
            {job.status === 'FAILED' && <p className="status-message error"><strong>Error:</strong> {job.error_message}</p>}
            
        </div>
        ) : (
          // Inference page component
          <InferencePage base_model={job.base_model}  job_id={job.id} hf_repo={`https://huggingface.co/${process.env.REACT_APP_HUGGING_FACE_USERNAME}/Finetuned-${job.new_model_name}`} onBack={() => setShowInferencePage(false)} />
        )}
      </div>
    </div>

    );
};

export default JobStatus;