import React from 'react';
import { motion } from 'framer-motion';
import { MapPin } from 'lucide-react';
import { ComposableMap, Geographies, Geography, Marker } from 'react-simple-maps';

interface MoroccoMapProps {
    cities: { name: string; count: number }[];
}

// Coordonnées géographiques réelles des villes (longitude, latitude)
const CITY_COORDINATES: Record<string, [number, number]> = {
    'Casablanca': [-7.6114, 33.5731],
    'Rabat': [-6.8498, 34.0209],
    'Fès': [-4.9998, 34.0181],
    'Marrakech': [-7.9811, 31.6295],
    'Tanger': [-5.8340, 35.7595],
    'Salé': [-6.7982, 34.0531],
    'Meknès': [-5.5471, 33.8935],
    'Oujda': [-1.9085, 34.6867],
    'Kenitra': [-6.5802, 34.2610],
    'Agadir': [-9.5981, 30.4278],
    'Tetouan': [-5.3684, 35.5889],
    'Temara': [-6.9063, 33.9280],
    'Safi': [-9.2372, 32.2994],
    'Mohammedia': [-7.3830, 33.6866],
    'Khouribga': [-6.9063, 32.8811],
    'El Jadida': [-8.5007, 33.2316],
    'Beni Mellal': [-6.3498, 32.3373],
    'Nador': [-2.9287, 35.1681],
    'Taza': [-4.0103, 34.2133],
    'Settat': [-7.6164, 33.0013],
    'Berrechid': [-7.5833, 33.2667],
    'Kénitra': [-6.5802, 34.2610],
    'Larache': [-6.1560, 35.1932],
    'Essaouira': [-9.7595, 31.5085],
    'Dakhla': [-15.9582, 23.7158],
    'Laayoune': [-13.2033, 27.1536],
    'Ouarzazate': [-6.9370, 30.9335],
    'Errachidia': [-4.4244, 31.9314],
    'Tiznit': [-9.7316, 29.6974],
    'Benguerir': [-7.9547, 32.2361],
    'Bouskoura': [-7.6500, 33.4500],
    'Nouaceur': [-7.5833, 33.3667],
    'Sidi Maarouf': [-7.6500, 33.5167],
};

// Fichier TopoJSON local du Maroc (cloné depuis GitHub)
const MOROCCO_GEOJSON = "/morocco-complete-map-geojson-topojson/morocco_map.topojson";

export const MoroccoMap = ({ cities }: MoroccoMapProps) => {
    const maxCount = Math.max(...cities.map(c => c.count), 1);
    const [hoveredCity, setHoveredCity] = React.useState<string | null>(null);

    return (
        <div className="relative w-full h-full bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-6 overflow-hidden">
            {/* Titre */}
            <div className="absolute top-4 left-4 z-10">
                <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                    <MapPin className="w-5 h-5 text-blue-600" />
                    Carte des Offres par Ville
                </h3>
            </div>

            {/* Contenu: Liste + Carte */}
            <div className="relative w-full h-full flex gap-4 pt-8">
                {/* Liste des villes à gauche */}
                <div className="w-52 flex-shrink-0 overflow-y-auto pr-2" style={{ maxHeight: '700px' }}>
                    <div className="space-y-1">
                        {cities
                            .filter(city => CITY_COORDINATES[city.name])
                            .sort((a, b) => b.count - a.count)
                            .map((city, index) => (
                                <motion.div
                                    key={city.name}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.03 }}
                                    onMouseEnter={() => setHoveredCity(city.name)}
                                    onMouseLeave={() => setHoveredCity(null)}
                                    className={`flex items-center justify-between px-2 py-1.5 rounded cursor-pointer transition-all ${hoveredCity === city.name
                                        ? 'bg-blue-100 shadow-sm'
                                        : 'hover:bg-slate-50'
                                        }`}
                                >
                                    <div className="flex items-center gap-2 flex-1 min-w-0">
                                        <div
                                            className="w-2 h-2 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex-shrink-0"
                                            style={{
                                                width: `${8 + (city.count / maxCount) * 8}px`,
                                                height: `${8 + (city.count / maxCount) * 8}px`,
                                            }}
                                        />
                                        <span className="text-xs font-medium text-slate-700 truncate">
                                            {city.name}
                                        </span>
                                    </div>
                                    <span className="text-xs font-bold text-blue-600 ml-2">
                                        {city.count}
                                    </span>
                                </motion.div>
                            ))}
                    </div>
                </div>

                {/* Carte */}
                <div className="flex-1 relative">
                    <ComposableMap
                        projection="geoMercator"
                        projectionConfig={{
                            scale: 2475,
                            center: [-9, 29],
                        }}
                        width={800}
                        height={650}
                        style={{ width: '100%', height: '100%' }}
                    >
                        <Geographies geography={MOROCCO_GEOJSON}>
                            {({ geographies }: { geographies: any[] }) =>
                                geographies.map((geo: any) => (
                                    <Geography
                                        key={geo.rsmKey}
                                        geography={geo}
                                        fill="url(#mapGradient)"
                                        stroke="#0ea5e9"
                                        strokeWidth={0.5}
                                        style={{
                                            default: { outline: 'none' },
                                            hover: { outline: 'none', fill: '#3b82f6', fillOpacity: 0.2 },
                                            pressed: { outline: 'none' },
                                        }}
                                    />
                                ))
                            }
                        </Geographies>

                        {/* Marqueurs des villes */}
                        {cities
                            .filter(city => CITY_COORDINATES[city.name])
                            .map((city, index) => {
                                const coordinates = CITY_COORDINATES[city.name];
                                const size = 20 + (city.count / maxCount) * 25;  // Équilibré: 20-45px au lieu de 12-48px
                                const isHovered = hoveredCity === city.name;

                                return (
                                    <Marker key={city.name} coordinates={coordinates}>
                                        <motion.g
                                            initial={{ scale: 0, opacity: 0 }}
                                            animate={{
                                                scale: isHovered ? 1.2 : 1,  // Agrandit au survol
                                                opacity: 1
                                            }}
                                            transition={{ delay: index * 0.05, type: 'spring' }}
                                            onMouseEnter={() => setHoveredCity(city.name)}
                                            onMouseLeave={() => setHoveredCity(null)}
                                            style={{
                                                cursor: 'pointer',
                                                zIndex: isHovered ? 1000 : index  // Au premier plan au survol
                                            }}
                                        >
                                            <circle
                                                r={size}
                                                fill="url(#markerGradient)"
                                                stroke="#fff"
                                                strokeWidth={isHovered ? 3 : 2}  // Bordure plus épaisse au survol
                                                className="transition-all"
                                                opacity={isHovered ? 1 : 0.85}  // Légère transparence par défaut
                                            />
                                            <text
                                                textAnchor="middle"
                                                y={1}
                                                style={{
                                                    fontFamily: 'system-ui',
                                                    fontSize: `${Math.max(size * 0.6, 10)}px`,  // Taille min 10px
                                                    fill: '#fff',
                                                    fontWeight: 'bold',
                                                    pointerEvents: 'none',
                                                }}
                                            >
                                                {city.count}
                                            </text>

                                            {/* Afficher le nom pour toutes les villes avec plus de 10 offres */}
                                            {(city.count > 10 || isHovered) && (
                                                <text
                                                    textAnchor="middle"
                                                    y={size + 19}
                                                    style={{
                                                        fontFamily: 'system-ui',
                                                        fontSize: isHovered ? '14px' : '12px',  // Plus grand au survol
                                                        fill: '#1e293b',
                                                        fontWeight: '700',
                                                        pointerEvents: 'none',
                                                        stroke: '#fff',
                                                        strokeWidth: '3px',
                                                        paintOrder: 'stroke',
                                                    }}
                                                >
                                                    {city.name}
                                                </text>
                                            )}
                                        </motion.g>
                                    </Marker>
                                );
                            })}

                        {/* Deuxième passage: Dessiner tous les tooltips au-dessus de tous les marqueurs */}
                        {cities
                            .filter(city => CITY_COORDINATES[city.name] && hoveredCity === city.name)
                            .map((city) => {
                                const coordinates = CITY_COORDINATES[city.name];
                                const size = 20 + (city.count / maxCount) * 25;

                                return (
                                    <Marker key={`tooltip-${city.name}`} coordinates={coordinates}>
                                        <g style={{ pointerEvents: 'none' }}>
                                            {/* Fond du tooltip */}
                                            <rect
                                                x={-80}
                                                y={-size - 70}
                                                width={160}
                                                height={60}
                                                fill="#1e293b"
                                                rx={8}
                                                opacity={0.95}
                                            />
                                            {/* Nom de la ville */}
                                            <text
                                                textAnchor="middle"
                                                y={-size - 45}
                                                style={{
                                                    fontFamily: 'system-ui',
                                                    fontSize: '18px',
                                                    fill: '#fff',
                                                    fontWeight: 'bold',
                                                }}
                                            >
                                                {city.name}
                                            </text>
                                            {/* Nombre d'offres */}
                                            <text
                                                textAnchor="middle"
                                                y={-size - 22}
                                                style={{
                                                    fontFamily: 'system-ui',
                                                    fontSize: '15px',
                                                    fill: '#cbd5e1',
                                                }}
                                            >
                                                {city.count} offres
                                            </text>
                                            {/* Flèche pointant vers le bas */}
                                            <polygon
                                                points={`0,${-size - 10} -8,${-size - 18} 8,${-size - 18}`}
                                                fill="#1e293b"
                                                opacity={0.95}
                                            />
                                        </g>
                                    </Marker>
                                );
                            })}

                        {/* Gradients */}
                        <defs>
                            <linearGradient id="mapGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                                <stop offset="100%" stopColor="#06b6d4" stopOpacity={0.1} />
                            </linearGradient>
                            <linearGradient id="markerGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stopColor="#3b82f6" />
                                <stop offset="100%" stopColor="#06b6d4" />
                            </linearGradient>
                        </defs>
                    </ComposableMap>
                </div>
            </div>

            {/* Légende */}
            <div className="absolute bottom-4 right-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-lg z-10">
                <div className="text-xs font-medium text-slate-600 mb-2">Nombre d'offres</div>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500"></div>
                    <span className="text-xs text-slate-500">Moins</span>
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500"></div>
                    <span className="text-xs text-slate-500">Plus</span>
                </div>
            </div>
        </div>
    );
};
