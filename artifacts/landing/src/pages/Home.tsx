import React from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { FaDiscord } from 'react-icons/fa';
import { 
  Zap, 
  Crown, 
  Trophy, 
  Settings, 
  TerminalSquare, 
  Coins, 
  ShieldAlert,
  ArrowRight,
  Star,
  Users
} from 'lucide-react';
import { Link } from 'wouter';

// @ts-ignore
import heroBotImg from '@assets/generated_images/hero_bot.jpg';
// @ts-ignore
import rankCardImg from '@assets/generated_images/rank_card.jpg';
// @ts-ignore
import badgesImg from '@assets/generated_images/badges.jpg';
// @ts-ignore
import dashboardImg from '@assets/generated_images/dashboard.jpg';

const BOT_INVITE = "https://discord.com/oauth2/authorize";

// Add these visual components
const Nav = () => (
  <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 backdrop-blur-md bg-background/50 border-b border-border/50">
    <div className="flex items-center gap-2">
      <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center glow-primary">
        <Zap className="w-4 h-4 text-primary-foreground" />
      </div>
      <span className="font-serif font-bold text-xl tracking-tight">Server Levels+</span>
    </div>
    <div className="hidden md:flex items-center gap-8 text-sm font-medium text-muted-foreground">
      <a href="#features" className="hover:text-foreground transition-colors">Features</a>
      <a href="#economy" className="hover:text-foreground transition-colors">Economy</a>
      <a href="#dashboard" className="hover:text-foreground transition-colors">Dashboard</a>
    </div>
    <a 
      href={BOT_INVITE}
      target="_blank"
      rel="noopener noreferrer"
      className="px-4 py-2 rounded-full bg-white/10 hover:bg-white/20 text-white font-medium text-sm transition-all flex items-center gap-2 border border-white/10"
    >
      <FaDiscord className="w-4 h-4" />
      <span className="hidden sm:inline">Add to Discord</span>
    </a>
  </nav>
);

const Ticker = () => {
  return (
    <div className="w-full overflow-hidden bg-primary py-3 relative flex z-10 border-y border-white/10">
      <motion.div
        className="flex whitespace-nowrap gap-8 items-center"
        animate={{ x: [0, -1035] }}
        transition={{ repeat: Infinity, duration: 20, ease: "linear" }}
      >
        {[...Array(2)].map((_, i) => (
          <div key={i} className="flex gap-8 items-center">
            <span className="text-primary-foreground font-bold font-serif uppercase tracking-widest text-sm flex items-center gap-2">
              <Zap className="w-4 h-4" /> LEVEL UP YOUR COMMUNITY
            </span>
            <span className="text-primary-foreground/50 text-xl font-black">•</span>
            <span className="text-primary-foreground font-bold font-serif uppercase tracking-widest text-sm flex items-center gap-2">
              <Crown className="w-4 h-4" /> REWARD YOUR MEMBERS
            </span>
            <span className="text-primary-foreground/50 text-xl font-black">•</span>
            <span className="text-primary-foreground font-bold font-serif uppercase tracking-widest text-sm flex items-center gap-2">
              <Trophy className="w-4 h-4" /> CLIMB THE LEADERBOARD
            </span>
            <span className="text-primary-foreground/50 text-xl font-black">•</span>
            <span className="text-primary-foreground font-bold font-serif uppercase tracking-widest text-sm flex items-center gap-2">
              <Coins className="w-4 h-4" /> BUILD AN ECONOMY
            </span>
            <span className="text-primary-foreground/50 text-xl font-black">•</span>
          </div>
        ))}
      </motion.div>
    </div>
  );
};

const Hero = () => {
  return (
    <section className="relative min-h-[100dvh] flex items-center justify-center pt-20 overflow-hidden">
      <div className="absolute inset-0 bg-grid-pattern opacity-50"></div>
      
      {/* Glow blobs */}
      <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-primary/20 rounded-full blur-[120px] -z-10 mix-blend-screen" />
      <div className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-secondary/20 rounded-full blur-[150px] -z-10 mix-blend-screen" />
      
      <div className="container mx-auto px-6 relative z-10 grid lg:grid-cols-2 gap-12 items-center">
        <motion.div 
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="max-w-2xl"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary mb-6 text-sm font-medium">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            v3.0 is now live
          </div>
          
          <h1 className="text-5xl md:text-7xl font-black font-serif leading-[1.1] tracking-tight mb-6">
            Make your Discord <br/>
            <span className="text-gradient">feel alive.</span>
          </h1>
          
          <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-lg leading-relaxed">
            The ultimate leveling bot that turns your server into an addictive XP-powered community. Custom rank cards, economy, and beautiful web dashboards.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center gap-4">
            <a 
              href={BOT_INVITE}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full sm:w-auto px-8 py-4 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground font-bold text-lg transition-all glow-primary flex items-center justify-center gap-3 hover:scale-105 active:scale-95"
            >
              <FaDiscord className="w-6 h-6" />
              Add to Server
            </a>
            <a 
              href="#demo"
              className="w-full sm:w-auto px-8 py-4 rounded-full bg-card hover:bg-muted border border-border text-foreground font-medium text-lg transition-all flex items-center justify-center gap-2"
            >
              See Features <ArrowRight className="w-5 h-5" />
            </a>
          </div>
          
          <div className="mt-12 flex items-center gap-6 opacity-60">
            <div className="flex -space-x-4">
              {[1,2,3,4].map(i => (
                <div key={i} className="w-10 h-10 rounded-full border-2 border-background bg-muted flex items-center justify-center overflow-hidden">
                  <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${i}&backgroundColor=b6e3f4`} alt="avatar" />
                </div>
              ))}
            </div>
            <div className="text-sm font-medium">
              <strong className="text-foreground">10,000+</strong> servers leveled up
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9, rotateY: 15 }}
          animate={{ opacity: 1, scale: 1, rotateY: 0 }}
          transition={{ duration: 1, delay: 0.2 }}
          className="relative perspective-1000"
        >
          <div className="relative w-full aspect-[4/5] md:aspect-square max-w-md mx-auto transform-gpu group">
            <div className="absolute inset-0 bg-gradient-to-tr from-primary/30 to-secondary/30 rounded-3xl blur-2xl group-hover:blur-3xl transition-all duration-500" />
            <img 
              src={heroBotImg} 
              alt="Bot Interface" 
              className="relative rounded-3xl border border-white/10 shadow-2xl object-cover w-full h-full transform group-hover:scale-[1.02] transition-transform duration-500"
            />
            
            {/* Floating elements */}
            <motion.div 
              animate={{ y: [-10, 10, -10] }}
              transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
              className="absolute -right-6 top-20 p-4 rounded-2xl bg-card/80 backdrop-blur-xl border border-border shadow-xl flex items-center gap-4"
            >
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center text-white">
                <Trophy className="w-6 h-6" />
              </div>
              <div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider font-bold">New Level</div>
                <div className="text-lg font-black font-serif text-white">Level 42</div>
              </div>
            </motion.div>

            <motion.div 
              animate={{ y: [10, -10, 10] }}
              transition={{ repeat: Infinity, duration: 5, ease: "easeInOut" }}
              className="absolute -left-8 bottom-32 p-4 rounded-2xl bg-card/80 backdrop-blur-xl border border-border shadow-xl flex items-center gap-4"
            >
              <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary">
                <Zap className="w-5 h-5" />
              </div>
              <div>
                <div className="text-sm font-bold text-white">+150 XP</div>
                <div className="text-xs text-muted-foreground">Voice Channel</div>
              </div>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

const FeatureHighlight = ({ 
  direction = "left", 
  badge, 
  title, 
  description, 
  image, 
  features 
}: { 
  direction?: "left" | "right",
  badge: string,
  title: React.ReactNode,
  description: string,
  image: string,
  features: {icon: any, title: string, desc: string}[]
}) => {
  return (
    <section className="py-24 relative overflow-hidden">
      <div className="container mx-auto px-6">
        <div className={`flex flex-col ${direction === "left" ? "md:flex-row" : "md:flex-row-reverse"} gap-16 items-center`}>
          
          <motion.div 
            initial={{ opacity: 0, x: direction === "left" ? -50 : 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.8 }}
            className="flex-1 w-full"
          >
            <div className="relative group">
              <div className="absolute inset-0 bg-gradient-to-tr from-accent/20 to-primary/20 rounded-3xl blur-2xl group-hover:blur-3xl transition-all" />
              <img 
                src={image} 
                alt="Feature preview" 
                className="relative rounded-3xl border border-white/5 shadow-2xl w-full object-cover aspect-[4/3]"
              />
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, x: direction === "left" ? 50 : -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.8 }}
            className="flex-1"
          >
            <div className="inline-block px-3 py-1 rounded-full bg-white/5 border border-white/10 text-white mb-6 text-sm font-bold font-mono uppercase tracking-widest">
              {badge}
            </div>
            <h2 className="text-4xl md:text-5xl font-black font-serif mb-6 leading-[1.1]">
              {title}
            </h2>
            <p className="text-lg text-muted-foreground mb-8 leading-relaxed">
              {description}
            </p>
            
            <div className="space-y-6">
              {features.map((f, i) => (
                <div key={i} className="flex gap-4">
                  <div className="w-12 h-12 rounded-xl bg-card border border-border flex items-center justify-center shrink-0">
                    <f.icon className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-bold text-lg mb-1">{f.title}</h3>
                    <p className="text-muted-foreground text-sm leading-relaxed">{f.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

        </div>
      </div>
    </section>
  );
};

const CommandsGrid = () => {
  const commands = [
    { cmd: "/rank", desc: "View your beautiful generated rank card" },
    { cmd: "/leaderboard", desc: "Check who's dominating the server" },
    { cmd: "/shop", desc: "Spend coins on roles and custom items" },
    { cmd: "/daily", desc: "Claim your daily XP and coin rewards" },
    { cmd: "/prestige", desc: "Reset level for an exclusive badge" },
    { cmd: "/profile", desc: "Showcase your achievements and stats" },
  ];

  return (
    <section className="py-24 relative bg-card/30 border-y border-white/5">
      <div className="container mx-auto px-6 max-w-5xl text-center">
        <h2 className="text-4xl font-black font-serif mb-4">Slash Commands that pop.</h2>
        <p className="text-muted-foreground mb-12 max-w-2xl mx-auto">Native Discord slash commands with rich, interactive embeds and button components.</p>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {commands.map((c, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="p-6 rounded-2xl bg-background border border-border hover:border-primary/50 transition-colors text-left group"
            >
              <div className="font-mono text-primary font-bold text-lg mb-2 group-hover:text-secondary transition-colors">{c.cmd}</div>
              <div className="text-sm text-muted-foreground">{c.desc}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

const FinalCTA = () => {
  return (
    <section className="py-32 relative overflow-hidden flex items-center justify-center text-center">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent to-primary/10" />
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-full max-w-3xl h-[400px] bg-primary/20 blur-[150px] -z-10 rounded-full" />
      
      <div className="container mx-auto px-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <div className="w-20 h-20 mx-auto bg-primary rounded-3xl flex items-center justify-center glow-primary mb-8 rotate-12">
            <Zap className="w-10 h-10 text-white" />
          </div>
          <h2 className="text-5xl md:text-7xl font-black font-serif mb-6 tracking-tight">
            Ready to <span className="text-gradient">level up?</span>
          </h2>
          <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto">
            Join thousands of communities already using Server Levels+ to drive engagement and reward their members.
          </p>
          <a 
            href={BOT_INVITE}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-3 px-8 py-4 rounded-full bg-white text-black font-bold text-lg transition-all hover:scale-105 hover:bg-gray-200 active:scale-95"
          >
            <FaDiscord className="w-6 h-6 text-[#5865F2]" />
            Add to Discord — It's Free
          </a>
        </motion.div>
      </div>
    </section>
  );
};

const Footer = () => (
  <footer className="border-t border-white/10 py-12 bg-background relative z-10">
    <div className="container mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
      <div className="flex items-center gap-2">
        <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
          <Zap className="w-3 h-3 text-white" />
        </div>
        <span className="font-serif font-bold text-lg tracking-tight">Server Levels+</span>
      </div>
      <div className="text-muted-foreground text-sm">
        © {new Date().getFullYear()} Server Levels+. Not affiliated with Discord.
      </div>
      <div className="flex gap-6 text-sm font-medium">
        <a href="#" className="hover:text-primary transition-colors">Terms</a>
        <a href="#" className="hover:text-primary transition-colors">Privacy</a>
        <a href="#" className="hover:text-primary transition-colors">Support</a>
      </div>
    </div>
  </footer>
);


export default function Home() {
  return (
    <main className="min-h-screen bg-background relative">
      <div className="noise-overlay" />
      <Nav />
      <Hero />
      
      <div id="features">
        <Ticker />
        
        <FeatureHighlight 
          direction="left"
          badge="Progression"
          title={<>Cards that look like <span className="text-gradient">art.</span></>}
          description="Ditch the boring text embeds. Our generated rank cards are stunning visual centerpieces that players actually want to show off."
          image={rankCardImg}
          features={[
            { icon: Zap, title: "Message & Voice XP", desc: "Members earn points for chatting and hanging out in voice channels." },
            { icon: Crown, title: "Custom Backgrounds", desc: "Users can purchase custom backgrounds and colors from the shop." },
            { icon: ShieldAlert, title: "Anti-Spam Controls", desc: "Built-in cooldowns and rate limits prevent XP farming." }
          ]}
        />
        
        <FeatureHighlight 
          direction="right"
          badge="Economy"
          title={<>More than just <br/><span className="text-gradient-alt">levels.</span></>}
          description="A fully integrated economy system built right alongside progression. Earn coins, buy roles, and collect exclusive badges."
          image={badgesImg}
          features={[
            { icon: Coins, title: "Server Economy", desc: "Members earn coins for activity, daily claims, and weekly streaks." },
            { icon: Star, title: "Prestige System", desc: "Hit max level? Reset to prestige 1 and earn a permanent XP multiplier." },
            { icon: Trophy, title: "Auto-Achievements", desc: "Over 25 built-in achievements with beautiful notification cards." }
          ]}
        />

        <div id="dashboard">
          <FeatureHighlight 
            direction="left"
            badge="Admin"
            title={<>A dashboard that doesn't <span className="text-gradient">suck.</span></>}
            description="Configure your server exactly how you want it with our lightning-fast, beautiful web dashboard."
            image={dashboardImg}
            features={[
              { icon: Settings, title: "Granular Control", desc: "Adjust XP rates, set custom level roles, and manage ignored channels." },
              { icon: Users, title: "Member Management", desc: "Search members, edit balances, or manually set levels directly." },
              { icon: TerminalSquare, title: "Role Rewards", desc: "Automatically assign or remove Discord roles as members level up." }
            ]}
          />
        </div>
      </div>
      
      <CommandsGrid />
      <FinalCTA />
      <Footer />
    </main>
  );
}
