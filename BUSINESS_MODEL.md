# Doctown Business Model Options

## Current State
- Open-source CLI and agent framework
- Self-hostable with Docker
- Works with OpenAI API or Ollama (local LLMs)

## Monetization Strategy: Hybrid Freemium

### Free Tier (Self-Hosted)
- Full CLI access
- Self-host documenter with your own API keys or Ollama
- Create unlimited docpacks locally
- No cloud features

### Paid Tier ($8.99-$9.99/month/seat)
Choose your compute model:

#### Option A: Platform AI Credits (Recommended Entry)
- **Included AI processing**: 100 docpack generations/month on our infrastructure
- No API keys needed - we handle it
- Uses optimized Ollama models (fast, private, no rate limits)
- Overage: $0.10 per additional docpack

#### Option B: Bring Your Own Key (BYOK)
- Connect your OpenAI/Anthropic API key
- Unlimited processing (you pay API costs directly)
- We provide the infrastructure and workflow
- Best for power users with existing API subscriptions

### Premium Features (Both Plans)
1. **Cloud Storage & Sync**
   - Store docpacks in the cloud
   - Access from anywhere
   - Team sharing and collaboration

2. **GitHub Integration** 
   - Auto-document on PR/commit
   - Track documentation coverage
   - Diff-based updates (only document what changed)

3. **Commons Contributions**
   - Publish docpacks to public marketplace
   - Get discovered by others
   - Quality control (prevents spam/low-effort content)
   - Reputation system

4. **Advanced Features**
   - Custom agent prompts and tasks
   - Webhook integrations
   - API access for automation
   - Priority support

5. **Team Features** (add $5/seat after 3 seats)
   - Shared docpack libraries
   - Team permissions and roles
   - Usage analytics
   - Centralized billing

## Revenue Projections (Conservative)

### Target: $60k CAD/year (~$5k/month)
- **500 paid users @ $9.99/month** = $4,995/month
- Very achievable with a focused niche (devs who value documentation)
- Churn mitigation: lock-in through Commons contributions & GitHub integration

### Costs
- **Hosting (RunPod/Hetzner)**: ~$200/month for Ollama GPU instances
- **Storage (S3/Backblaze)**: ~$50/month for docpack storage
- **Infrastructure**: ~$100/month (web hosting, DB, CDN)
- **Total overhead**: ~$350/month (~7% of revenue at 500 users)

## Why This Works

### For Users
1. **Free tier is genuinely useful** - self-host everything, no gimping
2. **Paid tier adds convenience** - cloud, automation, collaboration
3. **BYOK option** - keeps power users happy, no vendor lock-in
4. **Fair pricing** - $9.99/month is coffee money for devs
5. **Commons as social proof** - see quality examples before subscribing

### For You
1. **Ollama = predictable costs** - no surprise API bills
2. **Multiple revenue streams** - subscriptions + BYOK markup
3. **Network effects** - Commons creates stickiness
4. **Open core = credibility** - builds trust, drives adoption
5. **Scalable** - Ollama on RunPod scales horizontally

## Implementation Phases

### Phase 1: MVP (Current)
- ✅ CLI works
- ✅ Ollama support
- 🚧 Web UI for upload/view
- Target: Launch free tier, validate product-market fit

### Phase 2: Cloud Platform (Month 2-3)
- User authentication
- Cloud storage for docpacks
- Basic team sharing
- Launch paid tier with Ollama credits

### Phase 3: GitHub Integration (Month 4-5)
- OAuth with GitHub
- Webhook listeners
- Automated documentation on commits
- This becomes the primary value prop

### Phase 4: Commons Marketplace (Month 6+)
- Public docpack library
- Search and discovery
- Quality ratings
- Contribution requirements (paid users only)

## Alternative: Enterprise Tier

If you get traction, add **Enterprise @ $99/month**:
- On-premise deployment
- SSO/SAML
- Custom models
- Dedicated support
- Compliance features (SOC2, etc.)

One enterprise customer = 10 indie subscriptions.

## Recommendation

Start with **Ollama by default** for the paid tier:
- Simple pricing
- No rate limits
- Better margins
- Add BYOK as "advanced" option later

Focus marketing on: 
- "Never hit rate limits again"
- "Your data never leaves our infrastructure"
- "Fast local AI processing"

This positions you as the **privacy-focused, developer-first** alternative to AI platforms.
