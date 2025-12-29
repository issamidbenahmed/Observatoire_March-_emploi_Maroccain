import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Search, MapPin, Building2, ExternalLink, Filter } from 'lucide-react';
import { api } from '../services/api';
import { ExportButton } from '../components/ExportButton';
import type { Job } from '../types';

const Jobs = () => {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [cityFilter, setCityFilter] = useState('');
    const [companyFilter, setCompanyFilter] = useState('');
    const [techFilter, setTechFilter] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    useEffect(() => {
        const fetchJobs = async () => {
            try {
                setLoading(true);
                const data = await api.getJobs({
                    page,
                    per_page: 20,
                    city: cityFilter || undefined,
                    company: companyFilter || undefined,
                    tech: techFilter || undefined,
                });
                setJobs(data.jobs);
                setTotalPages(data.pages);
            } catch (error) {
                console.error('Erreur lors du chargement des jobs:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchJobs();
    }, [page, cityFilter, techFilter, companyFilter]);

    // Client-side filtering for title only (since backend doesn't support generic search yet)
    const filteredJobs = jobs.filter(job =>
        job.title.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const getSourceColor = (source: string) => {
        const colors: Record<string, string> = {
            'dreamjob.ma': 'from-purple-500 to-pink-500',
            'emploi.ma': 'from-blue-500 to-cyan-500',
            'jobzyn.com': 'from-green-500 to-emerald-500',
            'forcemploi.ma': 'from-orange-500 to-red-500',
            'stagiaires.ma': 'from-yellow-500 to-orange-500',
            'indeed.com': 'from-indigo-500 to-purple-500',
            'bayt.com': 'from-teal-500 to-teal-600',
            'tanqeeb.com': 'from-indigo-500 to-blue-600',
        };
        return colors[source] || 'from-gray-500 to-gray-600';
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight text-foreground">Offres d'emploi</h2>
                    <p className="text-muted-foreground mt-1">Parcourez les dernières opportunités</p>
                </div>
                <ExportButton />
            </div>

            {/* Filtres */}
            <div className="grid gap-4 md:grid-cols-4">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="Titre du poste..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 rounded-lg bg-card border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                </div>
                <div className="relative">
                    <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="Entreprise..."
                        value={companyFilter}
                        onChange={(e) => setCompanyFilter(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 rounded-lg bg-card border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                </div>
                <div className="relative">
                    <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="Ville..."
                        value={cityFilter}
                        onChange={(e) => setCityFilter(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 rounded-lg bg-card border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                </div>
                <div className="relative">
                    <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="Technologie..."
                        value={techFilter}
                        onChange={(e) => setTechFilter(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 rounded-lg bg-card border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                </div>
            </div>

            {/* Liste des jobs */}
            {loading ? (
                <div className="text-center text-foreground py-12">Chargement des offres...</div>
            ) : (
                <div className="space-y-4">
                    {filteredJobs.map((job, idx) => (
                        <motion.div
                            key={job.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.05 }}
                            className="p-6 rounded-xl border border-border bg-card shadow-sm hover:shadow-md transition-all group"
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                        <h3 className="text-xl font-semibold text-foreground group-hover:text-primary transition-colors">
                                            {job.title}
                                        </h3>
                                        <span className={`px-3 py-1 rounded-full text-xs font-medium bg-gradient-to-r ${getSourceColor(job.source_site)} text-white`}>
                                            {job.source_site}
                                        </span>
                                    </div>

                                    <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
                                        <div className="flex items-center gap-1">
                                            <Building2 className="w-4 h-4" />
                                            <span>{job.company}</span>
                                        </div>
                                        <div className="flex items-center gap-1">
                                            <MapPin className="w-4 h-4" />
                                            <span>{job.location}</span>
                                        </div>
                                    </div>

                                    {/* Technologies */}
                                    {job.technologies && job.technologies.length > 0 && (
                                        <div className="flex flex-wrap gap-2 mb-2">
                                            {job.technologies.slice(0, 5).map((tech, i) => (
                                                <span
                                                    key={i}
                                                    className="px-2 py-1 rounded-md bg-blue-50 text-blue-700 text-xs font-medium border border-blue-200"
                                                >
                                                    {tech}
                                                </span>
                                            ))}
                                        </div>
                                    )}

                                    {/* Compétences */}
                                    {job.skills && job.skills.length > 0 && (
                                        <div className="flex flex-wrap gap-2">
                                            {job.skills.slice(0, 3).map((skill, i) => (
                                                <span
                                                    key={i}
                                                    className="px-2 py-1 rounded-md bg-purple-50 text-purple-700 text-xs font-medium border border-purple-200"
                                                >
                                                    {skill}
                                                </span>
                                            ))}
                                        </div>
                                    )}
                                </div>

                                <a
                                    href={job.url_offre}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-medium hover:shadow-lg hover:shadow-cyan-500/50 transition-all"
                                >
                                    Voir l'offre
                                    <ExternalLink className="w-4 h-4" />
                                </a>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="flex justify-center gap-2 mt-6">
                    <button
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="px-4 py-2 rounded-lg bg-card border border-border text-foreground disabled:opacity-50 disabled:cursor-not-allowed hover:bg-secondary transition-colors"
                    >
                        Précédent
                    </button>
                    <span className="px-4 py-2 text-foreground">
                        Page {page} sur {totalPages}
                    </span>
                    <button
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                        className="px-4 py-2 rounded-lg bg-card border border-border text-foreground disabled:opacity-50 disabled:cursor-not-allowed hover:bg-secondary transition-colors"
                    >
                        Suivant
                    </button>
                </div>
            )}
        </div>
    );
};

export default Jobs;
