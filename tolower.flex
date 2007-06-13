/* tolower.flex */

%%
[A-Z]	printf("%c", tolower(*yytext));
%%

