export function observe(reporter, operation, error) { reporter.report({request:operation.id,route:operation.route,message:error.message}); }
