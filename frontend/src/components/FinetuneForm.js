import React, { useState } from 'react';

const FinetuneForm = ({ onSubmit, isLoading }) => {
    const [file, setFile] = useState(null);
    const [baseModel, setBaseModel] = useState('unsloth/Phi-3-mini-4k-instruct-gguf');
    const [datasetType, setDatasetType] = useState('Q&A');
    const [newModelName, setNewModelName] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', file);
        formData.append('base_model', baseModel);
        formData.append('dataset_type', datasetType);
        formData.append('new_model_name', newModelName);
        onSubmit(formData);
    };

    return (
        <form onSubmit={handleSubmit}>
            <div className="form-group">
                <label htmlFor="file">Dataset (CSV with 'question' and 'answer' columns)</label>
                <input id="file" type="file" accept=".jsonl" onChange={(e) => setFile(e.target.files[0])} required />
            </div>
            <div className="form-group">
                <label htmlFor="baseModel">Base Model</label>
                <select id="baseModel" value={baseModel} onChange={(e) => setBaseModel(e.target.value)} required>
                    <option value="unsloth/Phi-3-mini-4k-instruct-gguf">Phi-3 Mini Instruct</option>
                    <option value="unsloth/llama-3-8b-Instruct">Llama 3 8B Instruct</option>                    
                </select>
            </div>
            <div className="form-group">
                <label htmlFor="newModelName">New Model Name on Hugging Face</label>
                <input id="newModelName" type="text" value={newModelName} onChange={(e) => setNewModelName(e.target.value)} placeholder="e.g., my-awesome-qa-model" required />
            </div>
            <button type="submit" disabled={isLoading || !file || !newModelName}>
                {isLoading ? 'Submitting...' : 'Start Finetuning'}
            </button>
        </form>
    );
};

export default FinetuneForm;