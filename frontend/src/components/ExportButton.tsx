import React from 'react';
import { api } from '../services/api';
import { Download } from 'lucide-react';

interface Props {
    className?: string;
}

export const ExportButton: React.FC<Props> = ({ className = '' }) => {
    const handleExport = () => {
        // Direct navigation to the download URL
        window.location.href = api.getExportUrl();
    };

    return (
        <button
            onClick={handleExport}
            className={`inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors shadow-sm ${className}`}
            title="Télécharger toutes les offres en CSV"
        >
            <Download size={18} />
            <span>Exporter CSV</span>
        </button>
    );
};
