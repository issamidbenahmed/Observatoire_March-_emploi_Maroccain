import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { History, BarChart3, TrendingUp, Play, LineChart } from 'lucide-react';
import { api } from '../services/api';
import {
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    BarChart, Bar, Legend,
    AreaChart, Area
} from 'recharts';

const HistoricalAnalysis = () => {
    const [jobsHistory, setJobsHistory] = useState<{ month: string; count: number }[]>([]);
    const [techHistory, setTechHistory] = useState<Record<string, number | string>[]>([]);
    const [loading, setLoading] = useState(true);
    const [scrapingStatus, setScrapingStatus] = useState<string | null>(null);

    // Palette de couleurs très distinctes et contrastées
    const colors = [
        "#FF6B6B", // Rouge vif
        "#4ECDC4", // Turquoise
        "#45B7D1", // Bleu ciel
        "#FFA07A", // Saumon
        "#98D8C8", // Vert menthe
        "#F7DC6F", // Jaune doré
        "#BB8FCE", // Violet
        "#85C1E2", // Bleu clair
        "#F8B739", // Orange
        "#52B788", // Vert
        "#E63946", // Rouge foncé
        "#A8DADC", // Bleu pâle
        "#F4A261", // Orange brûlé
        "#2A9D8F", // Vert sarcelle
        "#E76F51", // Terracotta
        "#264653", // Bleu marine
        "#E9C46A", // Jaune moutarde
        "#F72585", // Rose vif
        "#7209B7", // Violet foncé
        "#3A0CA3"  // Bleu indigo
    ];

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [jobs, techs] = await Promise.all([
                api.getJobsHistory(),
                api.getTechHistory()
            ]);
            setJobsHistory(jobs);
            setTechHistory(techs);
        } catch (error) {
            console.error('Erreur chargement historique:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleRunScraper = async () => {
        if (!confirm("Attention : Le scraping historique est intensif et peut prendre plusieurs minutes. Voulez-vous continuer ?")) {
            return;
        }
        try {
            setScrapingStatus("Lancement...");
            const res = await api.runEnhancedScraping();
            setScrapingStatus(res.message);
            setTimeout(() => setScrapingStatus(null), 5000);
        } catch (error) {
            setScrapingStatus("Erreur au lancement");
            console.error(error);
        }
    };

    const totalJobsScraped = jobsHistory.reduce((acc, curr) => acc + curr.count, 0);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-2xl text-foreground animate-pulse">Chargement de l'analyse historique...</div>
            </div>
        );
    }

    // Extraire les noms de technologies dynamiquement pour le graphe empilé/lignes
    const allTechKeys = techHistory.length > 0 ? Object.keys(techHistory[0]).filter(k => k !== 'month') : [];

    // Calculer la somme totale pour chaque technologie pour garder les plus importantes
    const techTotals = allTechKeys.map(key => ({
        name: key,
        total: techHistory.reduce((sum, month) => sum + (Number(month[key]) || 0), 0)
    }));

    // Trier et garder les 10 plus importantes
    const topTechs = techTotals
        .sort((a, b) => b.total - a.total)
        .slice(0, 10)
        .map(t => t.name);

    const techKeys = topTechs;

    return (
        <div className="space-y-8 pb-10">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-3">
                        <History className="w-8 h-8 text-blue-600" />
                        Analyse Historique (10 mois +)
                    </h2>
                    <p className="text-muted-foreground mt-1">
                        Visualisation de l'évolution du marché sur la longue durée.
                    </p>
                </div>

                <button
                    onClick={handleRunScraper}
                    className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-lg shadow-md transition-all hover:scale-[1.02] active:scale-[0.98]"
                >
                    <Play className="w-4 h-4" />
                    Lancer Scraping Deep (Historique)
                </button>
            </div>

            {scrapingStatus && (
                <div className="p-4 bg-blue-50 text-blue-700 border border-blue-200 rounded-lg">
                    Information: {scrapingStatus}
                </div>
            )}



            {/* KPI Cards */}
            <div className="grid gap-4 md:grid-cols-3">
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="p-6 rounded-xl bg-white border border-slate-200 shadow-sm">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-blue-100 rounded-lg">
                            <BarChart3 className="w-6 h-6 text-blue-600" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-500">Total Offres Analysées</p>
                            <h3 className="text-2xl font-bold text-slate-900">{totalJobsScraped}</h3>
                        </div>
                    </div>
                </motion.div>

                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="p-6 rounded-xl bg-white border border-slate-200 shadow-sm">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-purple-100 rounded-lg">
                            <TrendingUp className="w-6 h-6 text-purple-600" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-500">Mois le plus Actif</p>
                            <h3 className="text-2xl font-bold text-slate-900">
                                {jobsHistory.length > 0
                                    ? jobsHistory.reduce((prev, current) => (prev.count > current.count) ? prev : current).month
                                    : "-"}
                            </h3>
                        </div>
                    </div>
                </motion.div>

                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="p-6 rounded-xl bg-white border border-slate-200 shadow-sm">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-green-100 rounded-lg">
                            <LineChart className="w-6 h-6 text-green-600" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-500">Technologies Suivies</p>
                            <h3 className="text-2xl font-bold text-slate-900">{techKeys.length}</h3>
                        </div>
                    </div>
                </motion.div>
            </div>

            {/* Charts Section */}
            <div className="grid gap-6">

                {/* Evolution des Offres */}
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="p-6 rounded-xl bg-white border border-slate-200 shadow-sm">
                    <h3 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-blue-600" />
                        Évolution du Volume d'Offres (Par Mois)
                    </h3>
                    <div className="h-[350px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={jobsHistory} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                                <XAxis
                                    dataKey="month"
                                    stroke="#94a3b8"
                                    minTickGap={40}
                                    tick={{ fontSize: 12 }}
                                />
                                <YAxis
                                    stroke="#94a3b8"
                                    tick={{ fontSize: 12 }}
                                    label={{ value: "Nombre d'offres", angle: -90, position: 'insideLeft', offset: 10, fill: '#94a3b8', fontSize: 12 }}
                                />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                                />
                                <Bar dataKey="count" fill="#3b82f6" name="Nombre d'offres" radius={[8, 8, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>

                {/* Evolution des Technologies (Stacked Area for better trend visual) */}
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} className="p-6 rounded-xl bg-white border border-slate-200 shadow-sm">
                    <h3 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-indigo-600" />
                        Évolution des Techs Dominantes (Area Tech Trends)
                    </h3>
                    <div className="h-[400px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={techHistory} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                <defs>
                                    {techKeys.map((key, index) => (
                                        <linearGradient key={`grad-${key}`} id={`grad-${key}`} x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor={colors[index % colors.length]} stopOpacity={0.4} />
                                            <stop offset="95%" stopColor={colors[index % colors.length]} stopOpacity={0} />
                                        </linearGradient>
                                    ))}
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                                <XAxis
                                    dataKey="month"
                                    stroke="#94a3b8"
                                    minTickGap={40}
                                    tick={{ fontSize: 12 }}
                                />
                                <YAxis
                                    stroke="#94a3b8"
                                    tick={{ fontSize: 12 }}
                                    label={{ value: "Cumul mentions", angle: -90, position: 'insideLeft', offset: 10, fill: '#94a3b8', fontSize: 12 }}
                                />
                                <Tooltip
                                    itemSorter={(item) => -(item.value as number)}
                                    contentStyle={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                />
                                <Legend />
                                {techKeys.map((key, index) => (
                                    <Area
                                        key={key}
                                        type="monotone"
                                        dataKey={key}
                                        stackId="1"
                                        stroke={colors[index % colors.length]}
                                        fill={`url(#grad-${key})`}
                                        strokeWidth={2}
                                    />
                                ))}
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>

                {/* Distribution Technologies (Stacked Bar) */}
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }} className="p-6 rounded-xl bg-white border border-slate-200 shadow-sm">
                    <h3 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-slate-500" />
                        Distribution Mensuelle des Technologies
                    </h3>
                    <div className="h-[400px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={techHistory} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                                <XAxis
                                    dataKey="month"
                                    stroke="#94a3b8"
                                    tick={{ fontSize: 12 }}
                                    minTickGap={30}
                                />
                                <YAxis
                                    stroke="#94a3b8"
                                    tick={{ fontSize: 12 }}
                                    label={{ value: "Cumul mentions", angle: -90, position: 'insideLeft', offset: 10, fill: '#94a3b8', fontSize: 12 }}
                                />
                                <Tooltip
                                    itemSorter={(item) => -(item.value as number)}
                                    cursor={{ fill: '#f1f5f9' }}
                                    contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                                />
                                <Legend />
                                {techKeys.map((key, index) => (
                                    <Bar
                                        key={key}
                                        dataKey={key}
                                        stackId="a"
                                        fill={colors[index % colors.length]}
                                    />
                                ))}
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>

            </div>
        </div>
    );
};

export default HistoricalAnalysis;
