import passport from 'passport'
import type { Express } from 'express'
import type {
  AuthStrategyBuilder,
  AuthStrategyMetadata,
  AuthStrategyPassportUser
} from '@/modules/auth/helpers/types'
import type { CreateAuthorizationCode } from '@/modules/auth/domain/operations'
import {
  finalizeAuthMiddlewareFactory,
  moveAuthParamsToSessionMiddlewareFactory,
  sessionMiddlewareFactory
} from '@/modules/auth/middleware'
import type { LegacyGetUser } from '@/modules/core/domain/users/operations'
import type { EventBusEmit } from '@/modules/shared/services/eventBus'
import { ensureError } from '@speckle/shared'
import { moduleLogger } from '@/observability/logging'

const setupStrategiesFactory =
  (deps: {
    githubStrategyBuilder: AuthStrategyBuilder
    azureAdStrategyBuilder: AuthStrategyBuilder
    googleStrategyBuilder: AuthStrategyBuilder
    localStrategyBuilder: AuthStrategyBuilder
    oidcStrategyBuilder: AuthStrategyBuilder
    createAuthorizationCode: CreateAuthorizationCode
    getUser: LegacyGetUser
    emitEvent: EventBusEmit
  }) =>
  async (app: Express) => {
    passport.serializeUser((user, done) => done(null, user))
    passport.deserializeUser((user, done) =>
      done(null, user as AuthStrategyPassportUser)
    )

    app.use(passport.initialize())

    const sessionMiddleware = sessionMiddlewareFactory()
    const moveAuthParamsToSessionMiddleware = moveAuthParamsToSessionMiddlewareFactory()
    const finalizeAuthMiddleware = finalizeAuthMiddlewareFactory({ ...deps })

    /*
     * Strategies initialisation & listing
     */

    const enabledBuilders: AuthStrategyBuilder[] = []

    if (process.env.STRATEGY_GOOGLE === 'true') {
      enabledBuilders.push(deps.googleStrategyBuilder)
    }

    if (process.env.STRATEGY_GITHUB === 'true') {
      enabledBuilders.push(deps.githubStrategyBuilder)
    }

    if (process.env.STRATEGY_AZURE_AD === 'true') {
      enabledBuilders.push(deps.azureAdStrategyBuilder)
    }

    if (process.env.STRATEGY_OIDC === 'true') {
      enabledBuilders.push(deps.oidcStrategyBuilder)
    }

    // Note: always leave the local strategy init for last so as to be able to
    // force enable it in case no others are present.
    if (process.env.STRATEGY_LOCAL === 'true' || !enabledBuilders.length) {
      enabledBuilders.push(deps.localStrategyBuilder)
    }

    // Initialize strategies with error handling - don't crash if one fails
    const authStrategies: AuthStrategyMetadata[] = []
    for (const builder of enabledBuilders) {
      try {
        const strategy = await builder(
          app,
          sessionMiddleware,
          moveAuthParamsToSessionMiddleware,
          finalizeAuthMiddleware
        )
        authStrategies.push(strategy)
      } catch (err) {
        const error = ensureError(err, 'Failed to initialize auth strategy')
        moduleLogger.error(
          { err: error },
          'Failed to initialize authentication strategy. Skipping...'
        )
        // Continue with other strategies instead of crashing
      }
    }

    return authStrategies
  }

export default setupStrategiesFactory
