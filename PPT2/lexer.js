class Lexer {
    constructor() {
        this.keywordPython = /\b(def|class|if|elif|else|while|for|break|continue|return|import|from|as|pass|try|except|finally|with|in|is|and|or|not|True|False|None|global|nonlocal|lambda|yield)\b/;
        this.keywordCpp = /\b(int|float|double|char|void|bool|long|short|signed|unsigned|if|else|switch|case|default|for|while|do|break|continue|return|struct|class|public|private|protected|namespace|using|static|const|new|delete|sizeof|typedef)\b/;
    }

    buildRegex(language) {
        let regexKeyword = language === 'Python' ? this.keywordPython.source : this.keywordCpp.source;
        let regexComment = language === 'Python' ? /#.*/.source : /\/\/.*|\/\*[\s\S]*?\*\//.source;

        const tokenRules = [
            ['KOMENTAR', regexComment],
            ['STRING_LITERAL', /"(?:[^"\\\r\n]|\\.)*"|'(?:[^'\\\r\n]|\\.)*'/.source],
            ['RESERVE_WORD', regexKeyword],
            ['VARIABEL', /\b[a-zA-Z_][a-zA-Z0-9_]*\b/.source],
            ['ANGKA', /\b\d+\.\d+\b|\b\d+\b/.source],
            ['OPERATOR', /[+\-*/=<>!&|%^~]+/.source],
            ['SIMBOL_BACA', /[{}()\[\];,\.:]/.source],
            ['WHITESPACE', /\s+/.source],
            ['TIDAK_DIKENAL', /./.source]
        ];

        const combinedRegex = tokenRules.map(([name, pattern]) => `(?<${name}>${pattern})`).join('|');
        return new RegExp(combinedRegex, 'g');
    }

    analyze(sourceCode, language) {
        const masterRegex = this.buildRegex(language);
        const results = [];
        const lines = sourceCode.split(/\r?\n/);

        lines.forEach((line, index) => {
            const lineNumber = index + 1;
            let match;
            // Reset lastIndex for each line to ensure consistent behavior
            masterRegex.lastIndex = 0;
            
            while ((match = masterRegex.exec(line)) !== null) {
                const groups = match.groups;
                const tokenType = Object.keys(groups).find(key => groups[key] !== undefined);
                const value = match[0];

                if (tokenType === 'WHITESPACE') continue;

                let category = "";
                if (tokenType === 'RESERVE_WORD') category = "Reserve words";
                else if (tokenType === 'SIMBOL_BACA') category = "Simbol dan tanda baca";
                else if (tokenType === 'VARIABEL') category = "Variabel";
                else if (tokenType === 'ANGKA' || tokenType === 'OPERATOR') category = "Kalimat matematika (Angka/Operator)";
                else if (tokenType === 'STRING_LITERAL') category = "Teks (String Literal)";
                else if (tokenType === 'KOMENTAR') category = "Komentar (Diabaikan Compiler)";
                else if (tokenType === 'TIDAK_DIKENAL') category = "TIDAK DIKENAL (ERROR)";

                results.push({ line: lineNumber, lexeme: value, category: category });
                
                // If regex matches an empty string (to prevent infinite loop, though our rules shouldn't)
                if (match.index === masterRegex.lastIndex) {
                    masterRegex.lastIndex++;
                }
            }
        });

        return results;
    }
}

// Export for use in HTML
window.Lexer = Lexer;
