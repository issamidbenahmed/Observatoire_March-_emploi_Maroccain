import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Briefcase, TrendingUp, Menu, History } from 'lucide-react';
import { cn } from '../lib/utils';
import { useState } from 'react';

const Layout = ({ children }: { children: React.ReactNode }) => {
    const location = useLocation();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    const navItems = [
        { name: 'Dashboard', path: '/', icon: LayoutDashboard },
        { name: 'Offres', path: '/jobs', icon: Briefcase },
        { name: 'Tendances', path: '/trends', icon: TrendingUp },
        { name: 'Analyse historique', path: '/history', icon: History },
    ];

    return (
        <div className="min-h-screen bg-background text-foreground flex overflow-hidden font-sans antialiased selection:bg-cyan-500/20">
            {/* Sidebar - Glassmorphism */}
            <aside className={cn(
                "fixed inset-y-0 left-0 z-50 w-64 bg-background/60 backdrop-blur-xl border-r border-border transition-transform duration-300 md:relative md:translate-x-0",
                isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
            )}>
                <div className="p-6 border-b border-border/50">
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-600 bg-clip-text text-transparent">
                        Observatoire
                    </h1>
                    <p className="text-xs text-muted-foreground mt-1">Marché de l'Emploi Maroc</p>
                </div>

                <nav className="p-4 space-y-2">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;

                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                onClick={() => setIsMobileMenuOpen(false)}
                                className={cn(
                                    "flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group relative overflow-hidden",
                                    isActive
                                        ? "text-primary bg-primary/10"
                                        : "text-muted-foreground hover:text-primary hover:bg-primary/5"
                                )}
                            >
                                {isActive && (
                                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-cyan-500 rounded-full" />
                                )}
                                <Icon className="w-5 h-5" />
                                <span className="font-medium">{item.name}</span>
                            </Link>
                        );
                    })}
                </nav>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col min-w-0 overflow-hidden bg-slate-50">
                {/* Header Mobile */}
                <header className="md:hidden flex items-center p-4 border-b border-border/40 bg-background/50 backdrop-blur-md">
                    <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}>
                        <Menu className="w-6 h-6" />
                    </button>
                    <span className="ml-4 font-bold">Menu</span>
                </header>

                <div className="flex-1 overflow-auto p-4 md:p-8 scroll-smooth">
                    <div className="max-w-7xl mx-auto">
                        {children}
                    </div>
                </div>
            </main>

            {/* Overlay for mobile */}
            {isMobileMenuOpen && (
                <div
                    className="fixed inset-0 z-40 bg-black/50 md:hidden backdrop-blur-sm"
                    onClick={() => setIsMobileMenuOpen(false)}
                />
            )}
        </div>
    );
};

export default Layout;
