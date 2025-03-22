// supabase/functions/ea-genai-assistant/index.ts

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { OpenAI } from 'https://esm.sh/openai@4.10.0'

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: Deno.env.get('OPENAI_API_KEY'),
})

// Initialize Supabase client with service role
const supabaseUrl = Deno.env.get('SUPABASE_URL') || ''
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || ''
const supabase = createClient(supabaseUrl, supabaseServiceKey)

interface RequestBody {
  query: string
  userId?: string
}

serve(async (req: Request) => {
  // CORS headers
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Content-Type': 'application/json',
  }

  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers })
  }

  try {
    // Parse request
    const { query, userId } = await req.json() as RequestBody

    if (!query) {
      return new Response(
        JSON.stringify({ error: 'Query parameter is required' }),
        { status: 400, headers }
      )
    }

    // Fetch relevant context from the EA repository
    // This helps the model provide more accurate and contextual responses
    const contextData = await fetchEAContext(query)
    
    // Create messages array with system prompt, context, and user query
    const messages = [
      {
        role: 'system',
        content: `You are an expert Enterprise Architecture assistant. 
You provide guidance on best practices, help analyze architecture models, and offer recommendations.
You have access to the organization's enterprise architecture repository.
Provide concise, practical, and actionable advice.`
      },
      {
        role: 'user',
        content: `Here is some context from our Enterprise Architecture repository: 
${JSON.stringify(contextData)}

My question is: ${query}`
      }
    ]

    // Call OpenAI Chat API
    const completion = await openai.chat.completions.create({
      model: 'gpt-4o',
      messages,
      temperature: 0.5,
      max_tokens: 1500,
    })

    // Get the response
    const response = completion.choices[0].message.content

    // Log the interaction for analytics
    if (userId) {
      await logInteraction(userId, query, response)
    }

    // Return the response
    return new Response(
      JSON.stringify({
        response: {
          final_output: response,
          query,
          timestamp: new Date().toISOString()
        }
      }),
      { headers }
    )
  } catch (error) {
    console.error('Error in EA GenAI Assistant:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers }
    )
  }
})

/**
 * Fetch relevant context from the EA repository based on the query
 */
async function fetchEAContext(query: string) {
  try {
    // Process the query to extract key terms
    const keyTerms = extractKeyTerms(query)
    
    // Set up a context object to store relevant information
    const context = {
      elements: [],
      models: [],
      domains: [],
      relationships: []
    }
    
    // Search for relevant elements
    const { data: elements, error: elementsError } = await supabase
      .from('ea_elements')
      .select('id, name, description, domain, type, properties')
      .or(keyTerms.map(term => `name.ilike.%${term}%`).join(','))
      .limit(10)
    
    if (elementsError) {
      console.error('Error fetching elements:', elementsError)
    } else {
      context.elements = elements || []
    }
    
    // Search for relevant models
    const { data: models, error: modelsError } = await supabase
      .from('ea_models')
      .select('id, name, description, status')
      .or(keyTerms.map(term => `name.ilike.%${term}%`).join(','))
      .limit(5)
    
    if (modelsError) {
      console.error('Error fetching models:', modelsError)
    } else {
      context.models = models || []
    }
    
    // If we have element IDs, fetch related relationships
    if (context.elements.length > 0) {
      const elementIds = context.elements.map(e => e.id)
      const { data: relationships, error: relationshipsError } = await supabase
        .from('ea_relationships')
        .select('id, name, description, source_element_id, target_element_id, type')
        .or(`source_element_id.in.(${elementIds.join(',')}),target_element_id.in.(${elementIds.join(',')})`)
        .limit(20)
      
      if (relationshipsError) {
        console.error('Error fetching relationships:', relationshipsError)
      } else {
        context.relationships = relationships || []
      }
    }
    
    return context
  } catch (error) {
    console.error('Error fetching EA context:', error)
    return {}
  }
}

/**
 * Extract key terms from a query for context searching
 */
function extractKeyTerms(query: string): string[] {
  // Remove common words and punctuation
  const stopWords = ['the', 'and', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'about', 'is', 'are']
  
  // Convert to lowercase and split into words
  const words = query.toLowerCase().split(/\W+/)
  
  // Filter out stop words and short words
  const filteredTerms = words.filter(
    word => word.length > 2 && !stopWords.includes(word)
  )
  
  // Get unique terms
  return [...new Set(filteredTerms)]
}

/**
 * Log user interactions for analytics
 */
async function logInteraction(userId: string, query: string, response: string) {
  try {
    const { error } = await supabase
      .from('ea_genai_interactions')
      .insert([
        {
          user_id: userId,
          query,
          response: response,
          created_at: new Date().toISOString()
        }
      ])
    
    if (error) {
      console.error('Error logging interaction:', error)
    }
  } catch (error) {
    console.error('Error in logging interaction:', error)
  }
}
